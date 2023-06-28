import argparse
import os
import shutil
import sys
import pathlib
import time
import json
import functools
import re
import unicodedata
import http.client
import xml.etree.ElementTree as ET

# Paths needed from the workspace
usrdir = os.getcwd()
os.chdir(os.path.dirname(__file__))

src = "src"
res = "res"
dest = "site"
dist = "dist"

# The port where you want to run localhost test server
serverPort = 24580

# The format of date and time to add on docs
timeformat = "%A, %B %d %Y"
updatetimeformat = "%d-%m-%Y"

# apply basic config on logger, level to info
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.root

# Prepare arguments from the terminal
parser = argparse.ArgumentParser(description="Your developer toolkit.", epilog="Tip:  Don't enter any argument to just build.")
parser.add_argument("--serve", "-s", action="store_true", help=f"Serve the website to localhost:{ serverPort }.")
parser.add_argument("--build", "-b", action="store_true", help="Override to build the source files.")
parser.add_argument("--debug", "-t", action="store_true", help="Build the site in debug mode (enables eruda console).")
parser.add_argument("--clean", "-c", action="store_true", help="Remove the last build first before doing any actions on it.")
parser.add_argument("--watch", "-w", action="store_true", help="Watch for any file changes on src and res folder while editing it.")
parser.add_argument("--deploy", "-d", action="store_true", help="Deploy the built output to GitHub Pages.")
parser.add_argument("--pack", "-p", action="store_true", help="Package the output into archives for release.")
subparsers = parser.add_subparsers(dest="subcmd", help="sub-commands")
parser_import = subparsers.add_parser("import", help="Import directory")
parser_import.add_argument("folder", metavar="<folder>", help="Path where docs are from")
parser_import.add_argument("dest", metavar="<dest>", help="Path where you want to place the docs in src folder")
args = parser.parse_args()

config = {
  "debug": args.debug
}

if args.subcmd == "import":
  importpath = pathlib.Path(os.path.normpath(os.path.join(usrdir, args.folder)))
  importdest = pathlib.Path(os.path.normpath(os.path.join("src", args.dest)))

def import_docs(debug=False):
  if args.subcmd == "import":
    try:
      shutil.copytree(importpath, importdest)
      if debug: print("Imported successfully")
    except:
      if debug: print("Import failed")

# Utility function for safely deleting directory or file
def safe_delete(path):
  if os.path.exists(path):
    if os.path.isfile(path):
      os.unlink(path)
    else:
      shutil.rmtree(path)
    return True
  return False

# Performs cleanup if specified
if args.clean:
  print("Cleaning workspace...")
  safe_delete(dist)
  safe_delete(dest)
  print("Workspace cleaned.")

# Check important folders
if not os.path.exists(src): sys.exit("Source folder does not exists!")
if not os.path.exists(res): sys.exit("Resource folder does not exists!")

# Required third-party modules for building
try:
  import markdown
  from markdown.extensions import Extension as MarkdownBaseExtension
  from markdown.inlinepatterns import InlineProcessor as MarkdownInlineProcessor, \
    AsteriskProcessor as MarkdownSmartProcessor, \
    EmStrongItem as MarkdownSmartItem
  from markdown.blockprocessors import BlockProcessor as MarkdownBlockProcessor
  from markdown.treeprocessors import Treeprocessor as MarkdownTreeProcessor
except ImportError: sys.exit("Markdown module isn't installed. Did you setup the workspace?")

try:
  from pygments import highlight
  from pygments.lexers import get_lexer_for_filename, get_lexer_for_mimetype, get_lexer_by_name
  from pygments.formatters import HtmlFormatter
except ImportError: sys.exit("Pygments module isn't installed. Did you setup the workspace?")

try: import jinja2
except ImportError: sys.exit("Jinja2 module isn't installed. Did you setup the workspace?")

# load gemoji icon database
with open("emoji.json", "r", encoding="utf-8") as f:
  gemoji = json.load(f)

# some of this extension contents are from the source code of the markdown library

# emoticons processor
class IconInlineProcessor(MarkdownInlineProcessor):
  def __init__(self, *args, **kwargs):
    super().__init__(r":(\w+):", *args, **kwargs)
  
  def handleMatch(self, m, data):
    icon = m.group(1).lower()
    txt = gemoji[icon] if icon in gemoji else m.group(0)
    return txt, m.start(0), m.end(0)

# substitute html reserved characters and escape others (for utf-8 charset support)
class HTMLEntitiesInlineProcessor(MarkdownInlineProcessor):
  def __init__(self, subs, *args, **kwargs):
    self.replacements = subs
    self.replacements.update(self.DEFAULTS)
    
    regex = (
      r"(%s|["
      r"\u2200-\u22FF" # math symbols
      r"\u0370-\u03FF" # greek letters
      r"\u20A0-\u20CF" # currency symbols
      r"\u2190-\u21FF" # arrows
      r"\u2600-\u26FF" # misc symbols
      r"])" % ("|".join(self.replacements.keys()))
    )
    super().__init__(regex, re.UNICODE, *args, **kwargs)
  
  DEFAULTS = {
    # Common charcaters, see: https://www.w3schools.com/html/html_entities.asp
    "\u003C": "lt", # LESS THAN
    "\u003E": "gt", # GREATER THAN
    "\u0026": "amp", # AMPERSAND
    "\u0022": "quot", # DOUBLE QUOTATION MARKS
    "\u0027": "apos", # APOSTROPHE
    "\u00A9": "copy", # COPYRIGHT
    "\u00AE": "reg", # REGISTERED TRADEMARK
    "\u2122": "trade", # TRADEMARK
    # Math characters, see: https://www.w3schools.com/charsets/ref_utf_math.asp
    "\u2200": "forall", # FOR ALL
    "\u2202": "part", # PARTIAL DIFFERENTIAL
    "\u2203": "exist", # THERE EXISTS
    "\u2205": "empty", # EMPTY SET
    "\u2207": "nabla", # NABLA
    "\u2208": "isin", # ELEMENT OF
    "\u2209": "notin", # NOT AN ELEMENT OF
    "\u220B": "ni", # CONTAINS AS MEMBER
    "\u220F": "prod", # N-ARY PRODUCT
    "\u2211": "sum", # N-ARY SUMMATION
    "\u2212": "minus", # MINUS SIGN
    "\u2217": "lowast", # ASTERISK OPERATOR
    "\u221A": "radic", # SQUARE ROOT
    "\u221D": "prop", # PROPORTIONAL TO
    "\u221E": "infin", # INFINITY
    "\u2220": "ang", # ANGLE
    "\u2227": "and", # LOGICAL AND
    "\u2228": "or", # LOGICAL OR
    "\u2229": "cap", # INTERSECTION
    "\u222A": "cup", # UNION
    "\u222B": "int", # INTEGRAL
    "\u2234": "there4", # THEREFORE
    "\u223C": "sim", # TILDE OPERATOR
    "\u2245": "cong", # APPROXIMATELY EQUAL TO
    "\u2248": "asymp", # ALMOST EQUAL TO
    "\u2260": "ne", # NOT EQUAL TO
    "\u2261": "equiv", # IDENTICAL TO
    "\u2264": "le", # LESS-THAN OR EQUAL TO
    "\u2265": "ge", # GREATER-THAN OR EQUAL TO
    "\u2282": "sub", # SUBSET OF
    "\u2283": "sup", # SUPERSET OF
    "\u2284": "nsub", # NOT A SUBSET OF
    "\u2286": "sube", # SUBSET OF OR EQUAL TO
    "\u2287": "supe", # SUPERSET OF OR EQUAL TO
    "\u2295": "oplus", # CIRCLED PLUS
    "\u2297": "otimes", # CIRCLED TIMES
    "\u22A5": "perp", # UP TACK
    "\u22C5": "sdot", # DOT OPERATOR
    # Greek characters, see: https://www.w3schools.com/charsets/ref_utf_greek.asp
    "\u0391": "Alpha", # GREEK CAPITAL LETTER ALPHA
    "\u0392": "Beta", # GREEK CAPITAL LETTER BETA
    "\u0393": "Gamma", # GREEK CAPITAL LETTER GAMMA
    "\u0394": "Delta", # GREEK CAPITAL LETTER DELTA
    "\u0395": "Epsilon", # GREEK CAPITAL LETTER EPSILON
    "\u0396": "Zeta", # GREEK CAPITAL LETTER ZETA
    "\u0397": "Eta", # GREEK CAPITAL LETTER ETA
    "\u0398": "Theta", # GREEK CAPITAL LETTER THETA
    "\u0399": "Iota", # GREEK CAPITAL LETTER IOTA
    "\u039A": "Kappa", # GREEK CAPITAL LETTER KAPPA
    "\u039B": "Lambda", # GREEK CAPITAL LETTER LAMBDA
    "\u039C": "Mu", # GREEK CAPITAL LETTER MU
    "\u039D": "Nu", # GREEK CAPITAL LETTER NU
    "\u039E": "Xi", # GREEK CAPITAL LETTER XI
    "\u039F": "Omicron", # GREEK CAPITAL LETTER OMICRON
    "\u03A0": "Pi", # GREEK CAPITAL LETTER PI
    "\u03A1": "Rho", # GREEK CAPITAL LETTER RHO
    "\u03A3": "Sigma", # GREEK CAPITAL LETTER SIGMA
    "\u03A4": "Tau", # GREEK CAPITAL LETTER TAU
    "\u03A5": "Upsilon", # GREEK CAPITAL LETTER UPSILON
    "\u03A6": "Phi", # GREEK CAPITAL LETTER PHI
    "\u03A7": "Chi", # GREEK CAPITAL LETTER CHI
    "\u03A8": "Psi", # GREEK CAPITAL LETTER PSI
    "\u03A9": "Omega", # GREEK CAPITAL LETTER OMEGA
    "\u03B1": "alpha", # GREEK SMALL LETTER ALPHA
    "\u03B2": "beta", # GREEK SMALL LETTER BETA
    "\u03B3": "gamma", # GREEK SMALL LETTER GAMMA
    "\u03B4": "delta", # GREEK SMALL LETTER DELTA
    "\u03B5": "epsilon", # GREEK SMALL LETTER EPSILON
    "\u03B6": "zeta", # GREEK SMALL LETTER ZETA
    "\u03B7": "eta", # GREEK SMALL LETTER ETA
    "\u03B8": "theta", # GREEK SMALL LETTER THETA
    "\u03B9": "iota", # GREEK SMALL LETTER IOTA
    "\u03BA": "kappa", # GREEK SMALL LETTER KAPPA
    "\u03BB": "lambda", # GREEK SMALL LETTER LAMBDA
    "\u03BC": "mu", # GREEK SMALL LETTER MU
    "\u03BD": "nu", # GREEK SMALL LETTER NU
    "\u03BE": "xi", # GREEK SMALL LETTER XI
    "\u03BF": "omicron", # GREEK SMALL LETTER OMICRON
    "\u03C0": "pi", # GREEK SMALL LETTER PI
    "\u03C1": "rho", # GREEK SMALL LETTER RHO
    "\u03C2": "sigmaf", # GREEK SMALL LETTER FINAL SIGMA
    "\u03C3": "sigma", # GREEK SMALL LETTER SIGMA
    "\u03C4": "tau", # GREEK SMALL LETTER TAU
    "\u03C5": "upsilon", # GREEK SMALL LETTER UPSILON
    "\u03C6": "phi", # GREEK SMALL LETTER PHI
    "\u03C7": "chi", # GREEK SMALL LETTER CHI
    "\u03C8": "psi", # GREEK SMALL LETTER PSI
    "\u03C9": "omega", # GREEK SMALL LETTER OMEGA
    "\u03D1": "thetasym", # GREEK THETA SYMBOL
    "\u03D2": "upsih", # GREEK UPSILON WITH HOOK SYMBOL
    "\u03D5": "straightphi", # GREEK PHI SYMBOL
    "\u03D6": "piv", # GREEK PI SYMBOL
    "\u03DC": "Gammad", # GREEK LETTER DIGAMMA
    "\u03DD": "gammad", # GREEK SMALL LETTER DIGAMMA
    "\u03F0": "varkappa", # GREEK KAPPA SYMBOL
    "\u03F1": "varrho", # GREEK RHO SYMBOL
    "\u03F5": "straightepsilon", # GREEK LUNATE EPSILON SYMBOL
    "\u03F6": "backepsilon", # GREEK REVERSED LUNATE EPSILON SYMBOL
    # Currency symbols, see: https://www.w3schools.com/charsets/ref_utf_currency.asp
    "\u00A2": "cent", # CENT
    "\u00A3": "pound", # POUND
    "\u00A5": "yen", # YEN
    "\u20AC": "euro", # EURO
    # Arrows, see: https://www.w3schools.com/charsets/ref_utf_arrows.asp
    "\u2190": "larr", # LEFTWARDS ARROW
    "\u2191": "uarr", # UPWARDS ARROW
    "\u2192": "rarr", # RIGHTWARDS ARROW
    "\u2193": "darr", # DOWNWARDS ARROW
    "\u2194": "harr", # LEFT RIGHT ARROW
    "\u21B5": "crarr", # DOWNWARDS ARROW WITH CORNER LEFTWARDS
    "\u21D0": "lArr", # LEFTWARDS DOUBLE ARROW
    "\u21D1": "uArr", # UPWARDS DOUBLE ARROW
    "\u21D2": "rArr", # RIGHTWARDS DOUBLE ARROW
    "\u21D3": "dArr", # DOWNWARDS DOUBLE ARROW
    "\u21D4": "hArr", # LEFT RIGHT DOUBLE ARROW
    # Miscellaneous symbols, see: https://www.w3schools.com/charsets/ref_utf_symbols.asp
    "\u2660": "spades", # BLACK SPADE SUIT
    "\u2663": "clubs", # BLACK CLUB SUIT
    "\u2665": "hearts", # BLACK HEART SUIT
    "\u2666": "diams", # BLACK DIAMOND SUIT
  }
  
  def handleMatch(self, m, data):
    char = m.group(1)
    sub = "&%s;" % (self.replacements.get(char, "#" + str(ord(char))))
    return sub, m.start(0), m.end(0)

# inline element processor
class InlineElementProcessor(MarkdownInlineProcessor):
  def __init__(self, element, idx, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.element = element
    self.idx = idx
  
  def handleMatch(self, m, data):
    el = ET.Element(self.element)
    el.text = m.group(self.idx)
    return el, m.start(0), m.end(0)

# handle strikethrough and sub
class TildeInlineProcessor(MarkdownSmartProcessor):
  PATTERNS = [
      MarkdownSmartItem(re.compile(r'(~)\1{2}(.+?)\1(.*?)\1{2}', re.DOTALL | re.UNICODE), 'double', 'del,sub'),
      MarkdownSmartItem(re.compile(r'(~)\1{2}(.+?)\1{2}(.*?)\1', re.DOTALL | re.UNICODE), 'double', 'sub,del'),
      MarkdownSmartItem(re.compile(r'(?<!\w)(~)\1(?!\1)(.+?)(?<!\w)\1(?!\1)(.+?)\1{3}(?!\w)', re.DOTALL | re.UNICODE), 'double2', 'del,sub'),
      MarkdownSmartItem(re.compile(r'(?<!\w)(~{2})(?!~)(.+?)(?<!~)\1(?!\w)', re.DOTALL | re.UNICODE), 'single', 'del'),
      MarkdownSmartItem(re.compile(r'(~)(?!~)(.+?)(?<!~)\1', re.DOTALL | re.UNICODE), 'single', 'sub')
  ]

# create task lists like on GitHub Flavored Markdown
class TaskListBlockProcessor(MarkdownBlockProcessor):
  def __init__(self, *args):
    super().__init__(*args)
    self.INDENT = re.compile(r"^[ ]{%d,%d}(?<![^\s])(.*)" % (self.tab_length, self.tab_length * 2 - 1))
    self.ITEM = re.compile(r"^[*+-][ ]*\[(x| )\][ ]+?(.*)", re.IGNORECASE)
    self.TAB = " " * self.tab_length
  
  def test(self, parent, block):
    return bool(self.ITEM.match(block))
  
  def run(self, parent, blocks):
    block = blocks.pop(0)
    lines = []
    for line in block.split("\n"):
      item = self.ITEM.match(line)
      if item:
        lines.append([
          item.group(1).lower() == "x",
          item.group(2)
        ])
      elif self.INDENT.match(line):
        if lines[-1][1].startswith(self.TAB):
          lines[-1][1] = lines[-1][1] + "\n" + line[self.tab_length:]
        else:
          lines.append([ None, line ])
      else:
        lines[-1][1] = lines[-1][1] + "\n" + line
    sibling = self.lastChild(parent)
    
    if sibling is not None and sibling.tag == "ul":
      lst = sibling
      if lst[-1].text:
        p = ET.Element('p')
        p.text = lst[-1].text
        lst[-1].text = ''
        lst[-1].insert(0, p)
      lch = self.lastChild(lst[-1])
      if lch is not None and lch.tail:
        p = ET.SubElement(lst[-1], 'p')
        p.text = lch.tail.lstrip()
        lch.tail = ''
      li = ET.SubElement(lst, 'li')
      li.set("class", "taskitem")
      checkbox = ET.SubElement(li, "input")
      checkbox.set("type", "checkbox")
      checkbox.set("disabled", "")
      self.parser.state.set('looselist')
      ischecked, firstitem = lines.pop(0)
      if ischecked:
        checkbox.set("checked", "checked")
      self.parser.parseBlocks(li, [firstitem])
      self.parser.state.reset()
    elif parent.tag == "ul":
      lst = parent
    else:
      lst = ET.SubElement(parent, "ul")
      lst.set("class", "tasklist")
    
    self.parser.state.set("list")
    for check, content in lines:
      if content.startswith(self.TAB):
        self.parser.parseBlocks(lst[-1], [content[self.tab_length:]])
      elif check is not None:
        item = ET.SubElement(lst, "li")
        item.set("class", "taskitem")
        checkbox = ET.SubElement(item, "input")
        if check:
          checkbox.set("checked", "checked")
        checkbox.set("type", "checkbox")
        checkbox.set("disabled", "")
        self.parser.parseBlocks(item, [content])
    self.parser.state.reset()

# insert snippets from given links/filepaths
class SnippetsBlockProcessor(MarkdownBlockProcessor):
  def __init__(self, *args, **kwargs):
    super().__init__(*args)
    self.md = kwargs.get("md")
    
  # match an external snippet block, e.g.
  #   <@snippet>: file.txt
  # you can also specify line ranges:
  #   <@snippet>: file.txt:5:10  # matches file.txt and extract line 5 to line 10
  # file paths can be a URL, relative path or absolute path offsets on site folder
  RE = re.compile(
    r"^<@snippet>\s*\:\s*" # beginning '<@snippet>:'
    r"(?P<loc>" # location of the snippet file, can be a relative path or a url
    # match URL
    r"(?P<scheme>[+a-zA-Z]+:)?//" # scheme 'http:', 'ftp:', etc.
    r"(?P<hostname>[^<>/:]+)?" # hostname 'www.example.com'
    r"(\:(?P<port>\d+))?" # port of the URI '443', '8080', etc.
    r"(?P<req>(?P<path>/[^\#?;:]*)?" # file path 'filaneme.txt', '/foldername/filename.txt'
    r"(;(?P<param>[^\#?:]+))?" # url parameters ';text'
    r"(?P<query>\?[^\#:]+)?" # query parameters '?key=val&key2=val2'
    r"(?P<frag>\#[^:]+)?)" # fragment '#id', '#loc'
    # end URL
    r"|[^<>\:]+)\s*?" # the file is within the workspace
    r"\:?(?P<start>[+-]?\d+)?" # start line ':1'
    r"\:?(?P<end>[+-]?\d+)?$" # end line '::-1'
  )
  
  def test(self, parent, block):
    return bool(self.RE.match(block))
  
  def run(self, parent, blocks):
    block = blocks.pop(0)
    match = self.RE.match(block)
    
    mdloc = self.md.current_loc
    relloc = os.path.normpath(os.path.join(mdloc.parent, match.group("loc")))
    if os.path.isabs(relloc): relloc = relloc[1:]
    path = os.path.join(dest, relloc)
    
    try:
      # try to open the file
      with open(path, "r", encoding="utf-8") as f:
        srclines = f.read().split("\n")
      filename = os.path.split(match.group("loc"))[1]
      # set lexer based on the filename
      try:
        lexer = get_lexer_for_filename(filename)
      except:
        lexer = get_lexer_by_name("text")
    except FileNotFoundError:
      # file doesn't exists, try on internet
      try:
        loc = match.group("req")
        # connect to server and request the file
        conn = http.client.HTTPSConnection(match.group("hostname"))
        # handle redirects
        while True:
          conn.request("GET", loc)
          response = conn.getresponse()
          if loc := response.getheader("location"):
            # reset the connection to server
            conn.close()
            conn.connect()
            continue
          break
        # error was occured, raise so it will print the warning message
        if response.status >= 400:
          raise
        # For some servers, they sends Content-Type different from the mimetype of the
        # suffix of the requested file by the client. We will use here the Content-Type
        # header sent by the server to determine what lexer should we use to highlight
        # the snippet.
        content_type = { key: val for key, val in (item.strip().split("=") for item in ("mimetype=" + response.getheader("Content-Type", "text/plain; charset=utf-8")).split(";")) }
        try:
          lexer = get_lexer_for_mimetype(content_type["mimetype"])
        except:
          lexer = get_lexer_by_name("text")
        # decode the file and extract lines
        srclines = response.read().decode(encoding=content_type.get("charset", "utf-8")).split("\n")
        # get the filename
        filename = os.path.split(match.group("path"))[1]
        # close the connection to server
        conn.close()
      except:
        # give you warns if a requested snippet not found.
        print("\033[33mWarning\033[0m:  \033[31mCouldn't resolve external snippet at '%s' requested by document %s.\033[0m" % (match.group("loc"), mdloc))
        return
    
    # get lines
    start = match.group("start")
    if start: start = int(start) - 1
    else: start = 0
    if start < 0: start = len(srclines) + start # appropriate linenostart
    end = match.group("end")
    if end: end = int(end)
    else: end = len(srclines)
    # we have a scenario where start is higher than the end, handle it by swapping them
    if start > end:
      tmp = start
      start = end
      end = tmp
      del tmp
    
    # print snippet
    snippet = "\n".join(srclines[start:end])
    formatter = HtmlFormatter(cssclass="snippet", wrapcode=True, linenos=True, linenostart=start + 1)
    result = highlight(snippet, lexer, formatter)
    
    # put the snippet to tree
    div = ET.SubElement(parent, "div")
    div.set("class", "external-snippet")
    div.set("data-path", match.group(1))
    div.set("data-filename", filename)
    div.text = self.md.htmlStash.store(result)

# Tree processor to wrap block elements into a div, for handling overflows
class OverflowTreeProcessor(MarkdownTreeProcessor):
  def __init__(self, elem, cssclass, *args):
    super().__init__(*args)
    self.element_parents = ".//%s/.." % (elem)
    self.element_xpath = "./" + elem
    self.cssclass = cssclass
  
  def run(self, root):
    for parents in root.findall(self.element_parents):
      for el in parents.findall(self.element_xpath):
        parents.remove(el)
        div = ET.SubElement(parents, "div")
        div.set("class", self.cssclass)
        div.set("style", "overflow: auto;")
        div.append(el)

class CustomExtension(MarkdownBaseExtension):
  def extendMarkdown(self, md):
    md.registerExtension(self)
    self.md = md
    self.reset()
    # add to escaped chars
    md.ESCAPED_CHARS += ["~", "=", "*"]
    # inline processors
    md.inlinePatterns.register(IconInlineProcessor(md), "icons", 200)
    md.inlinePatterns.register(InlineElementProcessor("sup", 2, r"(\^)(?!\^)(.+?)(?<!\^)\1"), "sup", 40)
    md.inlinePatterns.register(InlineElementProcessor("mark", 2, r"(==)(?!==)(.+?)(?<!==)\1"), "mark", 30)
    md.inlinePatterns.register(TildeInlineProcessor(r"~"), "tilde", 40)
    md.inlinePatterns.register(HTMLEntitiesInlineProcessor({}), "entities", 95)
    # block processors
    md.parser.blockprocessors.register(TaskListBlockProcessor(md.parser), "tasklist", 100)
    md.parser.blockprocessors.register(SnippetsBlockProcessor(md.parser, md=md), "snippets", 110)
    # tree processors
    md.treeprocessors.register(OverflowTreeProcessor("table", "table", md), "handle_table_overflow", 50)
  
  def reset(self):
    self.md.current_loc = None

# Filter for templates to create relative url
@jinja2.pass_context
def url_filter(context, value):
  return str(pathlib.PosixPath(os.path.relpath(value, start=context["doc"]["location"])))[3:]

# Setup markdown and jinja2
md = markdown.Markdown(extensions=[CustomExtension(), "extra", "admonition", "toc", "meta", "sane_lists", "wikilinks", "codehilite", "smarty"], extension_configs={
  "extra": {
    "footnotes": {
      "PLACE_MARKER": "[FOOTNOTES]",
      "UNIQUE_IDS": True
    }
  },
  "toc": {
    "marker": "",
    "permalink": True,
    "permalink_title": "Permanent link to this reference."
  },
  "wikilinks": {
    "base_url": "/wiki/",
    "end_url": ".html"
  },
  "codehilite":{
    "css_class": "snippet"
  }
})
# you can still edit template files while in watch mode
env = jinja2.Environment(loader=jinja2.FileSystemLoader([res, src]), auto_reload=args.watch)
env.filters["url"] = url_filter
baseTmpl = env.get_template("base.tmpl")
sitemapTmpl = env.get_template("sitemap.tmpl")
indexTmplName = "template.tmpl"

# Load records of docs
recordsLoc = "_records.json"

if os.path.exists(recordsLoc):
  with open(recordsLoc, "r", encoding="utf-8") as f:
    records = json.load(f)
else: records = {}

# English stemmer for indexing
# See http://www.tartarus.org/~martin/PorterStemmer
class PorterStemmer:
    def __init__(self):
        self.b = ""  # buffer for word to be stemmed
        self.k = 0
        self.k0 = 0
        self.j = 0   # j is a general offset into the string
    
    def cons(self, i):
        if self.b[i] == 'a' or self.b[i] == 'e' or self.b[i] == 'i' or self.b[i] == 'o' or self.b[i] == 'u':
            return 0
        if self.b[i] == 'y':
            if i == self.k0:
                return 1
            else:
                return (not self.cons(i - 1))
        return 1
    
    def m(self):
        n = 0
        i = self.k0
        while 1:
            if i > self.j:
                return n
            if not self.cons(i):
                break
            i = i + 1
        i = i + 1
        while 1:
            while 1:
                if i > self.j:
                    return n
                if self.cons(i):
                    break
                i = i + 1
            i = i + 1
            n = n + 1
            while 1:
                if i > self.j:
                    return n
                if not self.cons(i):
                    break
                i = i + 1
            i = i + 1
    
    def vowelinstem(self):
        for i in range(self.k0, self.j + 1):
            if not self.cons(i):
                return 1
        return 0
    
    def doublec(self, j):
        if j < (self.k0 + 1):
            return 0
        if (self.b[j] != self.b[j-1]):
            return 0
        return self.cons(j)
    
    def cvc(self, i):
        if i < (self.k0 + 2) or not self.cons(i) or self.cons(i-1) or not self.cons(i-2):
            return 0
        ch = self.b[i]
        if ch == 'w' or ch == 'x' or ch == 'y':
            return 0
        return 1
    
    def ends(self, s):
        length = len(s)
        if s[length - 1] != self.b[self.k]: # tiny speed-up
            return 0
        if length > (self.k - self.k0 + 1):
            return 0
        if self.b[self.k-length+1:self.k+1] != s:
            return 0
        self.j = self.k - length
        return 1
    
    def setto(self, s):
        length = len(s)
        self.b = self.b[:self.j+1] + s + self.b[self.j+length+1:]
        self.k = self.j + length
    
    def r(self, s):
        if self.m() > 0:
            self.setto(s)
    
    def step1ab(self):
        if self.b[self.k] == 's':
            if self.ends("sses"):
                self.k = self.k - 2
            elif self.ends("ies"):
                self.setto("i")
            elif self.b[self.k - 1] != 's':
                self.k = self.k - 1
        if self.ends("eed"):
            if self.m() > 0:
                self.k = self.k - 1
        elif (self.ends("ed") or self.ends("ing")) and self.vowelinstem():
            self.k = self.j
            if self.ends("at"):   self.setto("ate")
            elif self.ends("bl"): self.setto("ble")
            elif self.ends("iz"): self.setto("ize")
            elif self.doublec(self.k):
                self.k = self.k - 1
                ch = self.b[self.k]
                if ch == 'l' or ch == 's' or ch == 'z':
                    self.k = self.k + 1
            elif (self.m() == 1 and self.cvc(self.k)):
                self.setto("e")
    
    def step1c(self):
        if (self.ends("y") and self.vowelinstem()):
            self.b = self.b[:self.k] + 'i' + self.b[self.k+1:]
    
    def step2(self):
        if self.b[self.k - 1] == 'a':
            if self.ends("ational"):   self.r("ate")
            elif self.ends("tional"):  self.r("tion")
        elif self.b[self.k - 1] == 'c':
            if self.ends("enci"):      self.r("ence")
            elif self.ends("anci"):    self.r("ance")
        elif self.b[self.k - 1] == 'e':
            if self.ends("izer"):      self.r("ize")
        elif self.b[self.k - 1] == 'l':
            if self.ends("bli"):       self.r("ble") # --DEPARTURE--
            # To match the published algorithm, replace this phrase with
            #   if self.ends("abli"):      self.r("able")
            elif self.ends("alli"):    self.r("al")
            elif self.ends("entli"):   self.r("ent")
            elif self.ends("eli"):     self.r("e")
            elif self.ends("ousli"):   self.r("ous")
        elif self.b[self.k - 1] == 'o':
            if self.ends("ization"):   self.r("ize")
            elif self.ends("ation"):   self.r("ate")
            elif self.ends("ator"):    self.r("ate")
        elif self.b[self.k - 1] == 's':
            if self.ends("alism"):     self.r("al")
            elif self.ends("iveness"): self.r("ive")
            elif self.ends("fulness"): self.r("ful")
            elif self.ends("ousness"): self.r("ous")
        elif self.b[self.k - 1] == 't':
            if self.ends("aliti"):     self.r("al")
            elif self.ends("iviti"):   self.r("ive")
            elif self.ends("biliti"):  self.r("ble")
        elif self.b[self.k - 1] == 'g': # --DEPARTURE--
            if self.ends("logi"):      self.r("log")
        # To match the published algorithm, delete this phrase
    
    def step3(self):
        if self.b[self.k] == 'e':
            if self.ends("icate"):     self.r("ic")
            elif self.ends("ative"):   self.r("")
            elif self.ends("alize"):   self.r("al")
        elif self.b[self.k] == 'i':
            if self.ends("iciti"):     self.r("ic")
        elif self.b[self.k] == 'l':
            if self.ends("ical"):      self.r("ic")
            elif self.ends("ful"):     self.r("")
        elif self.b[self.k] == 's':
            if self.ends("ness"):      self.r("")
    
    def step4(self):
        if self.b[self.k - 1] == 'a':
            if self.ends("al"): pass
            else: return
        elif self.b[self.k - 1] == 'c':
            if self.ends("ance"): pass
            elif self.ends("ence"): pass
            else: return
        elif self.b[self.k - 1] == 'e':
            if self.ends("er"): pass
            else: return
        elif self.b[self.k - 1] == 'i':
            if self.ends("ic"): pass
            else: return
        elif self.b[self.k - 1] == 'l':
            if self.ends("able"): pass
            elif self.ends("ible"): pass
            else: return
        elif self.b[self.k - 1] == 'n':
            if self.ends("ant"): pass
            elif self.ends("ement"): pass
            elif self.ends("ment"): pass
            elif self.ends("ent"): pass
            else: return
        elif self.b[self.k - 1] == 'o':
            if self.ends("ion") and (self.b[self.j] == 's' or self.b[self.j] == 't'): pass
            elif self.ends("ou"): pass
            # takes care of -ous
            else: return
        elif self.b[self.k - 1] == 's':
            if self.ends("ism"): pass
            else: return
        elif self.b[self.k - 1] == 't':
            if self.ends("ate"): pass
            elif self.ends("iti"): pass
            else: return
        elif self.b[self.k - 1] == 'u':
            if self.ends("ous"): pass
            else: return
        elif self.b[self.k - 1] == 'v':
            if self.ends("ive"): pass
            else: return
        elif self.b[self.k - 1] == 'z':
            if self.ends("ize"): pass
            else: return
        else:
            return
        if self.m() > 1:
            self.k = self.j
    
    def step5(self):
        self.j = self.k
        if self.b[self.k] == 'e':
            a = self.m()
            if a > 1 or (a == 1 and not self.cvc(self.k-1)):
                self.k = self.k - 1
        if self.b[self.k] == 'l' and self.doublec(self.k) and self.m() > 1:
            self.k = self.k -1
    
    def stem(self, p, i, j):
        self.b = p
        self.k = j
        self.k0 = i
        if self.k <= self.k0 + 1:
            return self.b # --DEPARTURE--
        
        self.step1ab()
        self.step1c()
        self.step2()
        self.step3()
        self.step4()
        self.step5()
        return self.b[self.k0:self.k+1]


# Utility function for dumping json with int keys
def jsonstringify(obj):
  if isinstance(obj, dict):
    return "{" + ",".join("%s:%s" % (jsonstringify(k), jsonstringify(v)) for k, v in obj.items()) +"}"
  if isinstance(obj, list):
    return "[" + ",".join(jsonstringify(el) for el in obj) + "]"
  if isinstance(obj, bool):
    return "true" if obj else "false"
  if isinstance(obj, int):
    return f"{obj}"
  if isinstance(obj, str):
    return json.dumps(obj)
  if obj == None:
    return "null"

# Utility function for remapping table of contents token from rendered markdowm page
def remap_toc(toclist):
  newtoc = []
  for item in toclist:
    childs = remap_toc(item["children"])
    del item["children"]
    newtoc.append(item)
    for child in childs:
      newtoc.append(child)
  return newtoc

# objects needed for indexing
codepoints = re.compile("[\\u0300-\\u036f]")
punct = re.compile("[\\s~`’‘|^°{}[\\]()<>\\\\%@#$&\\-+=/*\"':;!?.,]+")
replacements = [
  (re.compile("n't([ ,:;.!?]|$)"), ' not '),
  (re.compile("can't([ ,:;.!?]|$)"), 'can not '),
  (re.compile("'ll([ ,:;.!?]|$)"), ' will '),
  (re.compile("'s([ ,:;.!?]|$)"), ' is '),
  (re.compile("'re([ ,:;.!?]|$)"), ' are '),
  (re.compile("'ve([ ,:;.!?]|$)"), ' have '),
  (re.compile("'m([ ,:;.!?]|$)"), ' am '),
  (re.compile("'d([ ,:;.!?]|$)"), ' had ')
]
contractions = {
  "cannot": ['can', 'not'],
  "gonna": ['going', 'to'],
  "wanna": ['want', 'to']
}
stopwords = ["about","above","after","again","all","also","am","an","and",
  "another","any","are","as","at","be","because","been","before","being","below",
  "between","both","but","by","came","can","cannot","come","could","did","do",
  "does","doing","during","each","few","for","from","further","get","got","has",
  "had","he","have","her","here","him","himself","his","how","if","in","into",
  "is","it","its","itself","like","make","many","me","might","more","most","much",
  "must","my","myself","never","now","of","on","only","or","other","our","ours",
  "ourselves","out","over","own","said","same","see","should","since","so","some",
  "still","such","take","than","that","the","their","theirs","them","themselves",
  "then","there","these","they","this","those","through","to","too","under","until",
  "up","very","was","way","we","well","were","what","where","when","which","while",
  "who","whom","with","would","why","you","your","yours","yourself","a","b","c",
  "d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v",
  "w","x","y","z","_"
]
unicodeform = "NFD" # used on unicodedata.normalize
mdmetare = re.compile( # regex for removing metadata in markdown files
    r"^-{3}?(\s.*)?" # begin
    r"(\n[ ]{0,3}[A-Za-z0-9_-]+:\s*.*" # meta
    r"(\n[ ]{4,}.*)*?)*" # more
    r"\n(\n|(-{3}|\.{3})(\s.*)?)" # end
  , flags=re.M)
contributorre = re.compile(r"^([^\<]+)(\s+?\<([^\>]+)\>)?$")
separators = re.compile("[,\\s]+")

# instantiate stemmer
stemmer = PorterStemmer()

# Function for building every pages
def build_page(path, dx=None, tc=None, root=src, out=dest):
  
  path = str(path)
  
  if not path.endswith(".md"): return
  
  filepath = pathlib.Path(path)
  fileloc = filepath.relative_to(root)
  fileparent = fileloc.parent
  filesub = fileparent / (fileloc.stem + ".html")
  filedest = out / filesub
  pagetmpl = fileparent / (fileloc.stem + fileloc.suffix + ".tmpl")
  recordkey = str(fileloc)
  fileparent = str(fileparent)
  
  template = baseTmpl
  if os.path.exists(res / pagetmpl) or os.path.exists(src / pagetmpl):
    template = env.get_template(str(pagetmpl))
  else:
    for parent in fileloc.parents:
      tmplloc = parent / "template.tmpl"
      if os.path.exists(res / tmplloc) or os.path.exists(src / tmplloc):
        template = env.get_template(str(tmplloc))
        break
  
  if not recordkey in records: records[recordkey] = {
    "created": time.time()
  }
  
  # pass location to use in the extension
  md.current_loc = fileloc
  
  with open(path, "r", encoding="utf-8") as f:
    rawmd = f.read()
    docbody = md.convert(rawmd)
  
  # process keywords
  keywords = []
  if "keywords" in md.Meta:
    for kwl in md.Meta["keywords"]: # each lines
      for kwd in separators.split(kwl): # each keywords
        keywords.append(kwd)
  
  # process contributors list
  contributors = []
  if "contributors" in md.Meta:
    for person in md.Meta["contributors"]:
      match = contributorre.match(person)
      contributors.append({
        "name": match.group(1),
        "url": match.group(3)
      })
  
  context = {
    "title": md.Meta["title"][0] if "title" in md.Meta else "Untitled",
    "about": md.Meta["about"][0][0:160] if "about" in md.Meta else "No description.",
    "previous": md.Meta["previous"][0] + ".html" if "previous" in md.Meta else "",
    "next": md.Meta["next"][0] + ".html" if "next" in md.Meta else "",
    "contributors": contributors,
    "keywords": keywords,
    "home": fileloc.stem == "index",
    "location": str(fileloc.parent / fileloc.stem),
    "contents": remap_toc(md.toc_tokens),
    "created": time.strftime(timeformat, time.gmtime(records[recordkey]["created"])),
    "updated": time.strftime(timeformat, time.strptime(md.Meta["updated"][0], updatetimeformat) if "updated" in md.Meta else time.gmtime(records[recordkey]["created"]))
  }
  context["canonical"] = "https://vytdev.github.io/" + context["location"]
  
  context["data"] = json.dumps(context, separators=(",",":"))
  context["index"] = (True if md.Meta["index"] == "yes" else False) if "index" in md.Meta else True,
  context["toc"] = md.toc
  context["content"] = docbody
  context["indexCache"] = json.dumps({
    "@context": "https://schema.org",
    "@type":  "WebSite" if context["home"] and len(fileloc.parents) == 2 else "WebPage",
    "description": context["about"],
    "headline": context["title"],
    "name": context["title"],
    "url": context["canonical"]
  }, separators=(",",":"))
  
  with open(filedest, "w", encoding="utf-8") as f:
    f.write(template.render(doc=context, config=config))
  
  del context["content"]
  del context["toc"]
  del context["data"]
  del context["indexCache"]
  
  # add terms for indexing
  if context["index"] and dx != None and tc != None:
    docterms = {}
    termcount = 0
    
    # remove metadata
    rawmd = mdmetare.sub("", rawmd)
    
    # add important metadata to extract
    rawmd += "\n" + " ".join([
      context["title"],
      context["about"],
      context["created"],
      context["updated"],
      *(contributor["name"] for contributor in contributors),
      *context["keywords"]
    ])
    
    # normalize
    rawmd = unicodedata.normalize(unicodeform, rawmd)
    rawmd = codepoints.sub("", rawmd)
    
    # tokenize
    rawmd = rawmd.lower()
    for regex, repl in replacements: rawmd = regex.sub(repl, rawmd) # expand contractions with single quote
    rawtokens = punct.split(rawmd)
    tokens = []
    for rt in rawtokens:
      rt = rt.strip()
      if not rt: continue
      if rt in contractions:
        for t in contractions[rt]:
          tokens.append(t)
      else:
        tokens.append(rt)
    
    foundterms = []
    for t in list(tokens):
      # skip stopwords
      if t in stopwords: continue
      # stem
      t = stemmer.stem(t, 0, len(t) - 1)
      # store to index
      if not t in tc:
        pos = len(tc)
        dx["vocabulary"][pos] = t
        tc[t] = pos
      if not t in foundterms:
        dx["termdoc"][tc[t]] = dx["termdoc"].get(tc[t], 0) + 1
        foundterms.append(t)
      docterms[tc[t]] = docterms.get(tc[t], 0) + 1
      termcount += 1
    docterms["count"] = termcount
    context["terms"] = docterms
    dx["vocabulary"]["count"] += termcount
    
    # new document on index
    del context["index"]
    dx["docfiles"].append(context.copy())
  
  md.reset()
  
  context["recordkey"] = recordkey
  
  return context

# Copy all resource files
def copy_res(debug=False):
  # copy files in res folder one-by-one
  for root, dirs, files in os.walk(res):
    root = pathlib.Path(root)
    loc = root.relative_to(res)
    for folder in dirs:
      path = dest / loc / folder
      if not os.path.exists(path): os.makedirs(path)
      if debug: print("res folder : " + str(root / folder))
    for file in files:
      if file.endswith(".tmpl"):
        continue
      shutil.copyfile(root / file, dest / loc / file)
      if debug: print("res file   : " + str(root / file))

# Rebuild markdown and copy resource files
@functools.lru_cache(maxsize=None)
def rebuild_src(debug=False):
  global records
  buildtime = time.strftime("%a, %d %b %Y %H:%M:%S %z", time.localtime())
  termCache = {}
  dex = {
    "docfiles": [],
    "vocabulary": {
      "count": 0
    },
    "termdoc": {},
    "date": buildtime
  }
  pages = []
  newrecord = {}
  srcfilesnum = 0
  srcfoldersnum = 0
  
  for root, dirs, files in os.walk(src):
    root = pathlib.Path(root)
    loc = root.relative_to(src)
    
    # create directories
    for folder in dirs:
      path = dest / loc / folder
      if not os.path.exists(path): os.makedirs(path)
      if debug: print("src folder : " + str(root / folder))
      srcfoldersnum += 1
    
    # generate pages
    for file in files:
      fpath = root / file
      if not file.endswith(".md"):
        if not file.endswith(".tmpl"): shutil.copyfile(fpath, dest / loc / file)
        continue
      ctx = build_page(fpath, dex, termCache)
      recordkey = ctx["recordkey"]
      pages.append({
        "location": ctx["canonical"],
        "lastmod": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.strptime(ctx["updated"], timeformat))
      })
      if debug: print("src file   : " + str(fpath))
      srcfilesnum += 1
      newrecord[recordkey] = records[recordkey]
  
  records = newrecord
  
  dex["vocabulary"]["length"] = len(dex["vocabulary"]) - 1
  
  # create search index loader
  with open(os.path.join(dest, "assets", "dex.js"), "w", encoding="utf-8") as f:
    f.write("doc.index={}\n\n".format(jsonstringify(dex)))
  # create sitemap
  with open(os.path.join(dest, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write(sitemapTmpl.render(pages=pages))

# Function to rebuild the site
def update(debug=False, clean=False):
  # perform clean-up
  if clean: safe_delete(dest)
  if not os.path.exists(dest): os.makedirs(dest)
  
  # import docs
  import_docs()
  
  # copy resource files
  copy_res(debug)
  
  # process source
  rebuild_src(debug)

if args.debug:
  print("Building docs in debug mode.")

if args.subcmd == "import":
  print("Importing docs from '%s' to '%s'..." % (importpath, importdest))
  safe_delete(importdest)
  import_docs(debug=True)

# Override to rebuild the site or automatically rebuild the site if no one arguments were passed
if args.build or (not args.subcmd and not args.serve and not args.clean and not args.watch and not args.deploy and not args.pack):
  print("Generating docs...")
  start = time.monotonic()
  update(debug=True)
  print("The site has been built in %.3f seconds." % (time.monotonic() - start))

# Starts a filesystem observer for auto building
if args.watch:
  try:
    import watchdog.events as watcherEvents
    from watchdog.observers import Observer
  except ImportError: sys.exit("watchdog module isnt installed. Did you setup the workspace?")
  
  if not os.path.exists(dest): update()
  
  # collection of watchers
  watchers = []
  
  class BaseWatcher(watcherEvents.FileSystemEventHandler):
    """Base FS event handler"""
    def __init__(self, indir=src, outdir=dest, debug=False):
      self.indir = indir
      self.outdir = outdir
      self.debug = debug
      # start watching
      self.observer = Observer()
      self.observer.schedule(self, path=indir, recursive=True)
      self.observer.start()
      # push new watcher
      watchers.append(self)
    
    def stop(self):
      self.observer.stop()
      self.observer.join()
    
    def on_any_event(self, ev):
      """Handle all event types"""
      # report any events
      if self.debug:
        what = "directory" if ev.is_directory else "file"
        msg = "Unknown event!"
        if ev.event_type == watcherEvents.EVENT_TYPE_MOVED: msg = "Moved %s: from %s to %s" % (what, ev.src_path, ev.dest_path)
        elif ev.event_type == watcherEvents.EVENT_TYPE_CREATED: msg = "Created %s: %s" % (what, ev.src_path)
        elif ev.event_type == watcherEvents.EVENT_TYPE_MODIFIED: msg = "Modified %s: %s" % (what, ev.src_path)
        elif ev.event_type == watcherEvents.EVENT_TYPE_DELETED: msg = "Deleted %s: %s" % (what, ev.src_path)
        # only necessary events
        if not ev.event_type == watcherEvents.EVENT_TYPE_OPENED and not ev.event_type == watcherEvents.EVENT_TYPE_CLOSED:
          logger.info("watcher - %s", msg)
      # update paths
      ev.from_path = pathlib.Path(ev._src_path).relative_to(self.indir)
      if ev.event_type == watcherEvents.EVENT_TYPE_MOVED: ev.to_path = pathlib.Path(ev._dest_path).relative_to(self.indir)
    
    def on_moved(self, ev):
      shutil.move(self.outdir / ev.from_path, self.outdir / ev.to_path)
    
    def on_created(self, ev):
      if ev.is_directory: os.makedirs(self.outdir / ev.from_path)
      else: shutil.copyfile(self.indir / ev.from_path, self.outdir / ev.from_path)
    
    def on_modified(self, ev):
      if not ev.is_directory: self.on_created(ev)
    
    def on_deleted(self, ev):
      if ev.is_directory: safe_delete(self.outdir / ev.from_path)
      else: safe_delete(self.outdir / ev.from_path)
    
  
  class DocWatcher(BaseWatcher):
    """Base FS event handler"""
    def __init__(self, build, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.build = build
    
    def on_moved(self, ev):
      if self.build and not ev.is_directory and ev.from_path.suffix == ".md":
        pagepath = self.outdir / (ev.from_path.stem + ".html")
        if not ev.to_path.suffix == ".md":
          safe_delete(pagepath)
          shutil.copyfile(self.indir / ev.from_path, self.outdir / ev.to_path)
          try: del records[str(ev.from_path)]
          except: pass
        else: shutil.move(pagepath, self.outdir / (ev.from_path.stem + ".html"))
      elif ev.is_directory or not ev.from_path.suffix == ".tmpl": shutil.move(self.outdir / ev.from_path, self.outdir / ev.to_path)
    
    def on_created(self, ev):
      if ev.is_directory: os.makedirs(self.outdir / ev.from_path)
      elif self.build and ev.from_path.suffix == ".md": build_page(ev.src_path, root=self.indir, out=self.outdir)
      elif not ev.from_path.suffix == ".tmpl": shutil.copyfile(self.indir / ev.from_path, self.outdir / ev.from_path)
    
    def on_modified(self, ev):
      if not ev.is_directory:
        if self.build and ev.from_path.suffix == ".md": build_page(ev.src_path, root=self.indir, out=self.outdir)
        elif not ev.from_path.suffix == ".tmpl": shutil.copyfile(self.indir / ev.from_path, self.outdir / ev.from_path)
    
    def on_deleted(self, ev):
      if ev.is_directory: safe_delete(self.outdir / ev.from_path)
      elif self.build and ev.from_path.suffix == ".md":
        safe_delete(self.outdir / ev.from_path.parent / (ev.from_path.stem + ".html"))
        try: del records[str(ev.from_path)]
        except: pass
      elif not ev.from_path.suffix == ".tmpl": safe_delete(self.outdir / ev.from_path)
  
  # initialize observers
  DocWatcher(True, src, debug=True)
  DocWatcher(False, res, debug=True)
  
  if args.subcmd == "import":
    BaseWatcher(importpath, importdest)
  
  def stop_watching():
    for watcher in watchers: watcher.stop()
    print("Watch mode stopped.")
  

# Start a localhost server
# You can change the port where the server is ran, changing the variable at the top of
# this file called 'serverPort'.
if args.serve:
  # Snippets used in this block are from https://github.com/python/cpython/blob/3.11/Lib/http/server.py
  # with some modifications for improvement.
  from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
  from http import HTTPStatus
  import socket
  import html
  import contextlib
  import datetime
  import urllib
  import email
  
  if not os.path.exists(dest): update()
  
  class HTTPRequestHandler(SimpleHTTPRequestHandler):
    """Custom request handler"""
    protocol_version = "HTTP/1.0"
    
    def send_head(self):
      """Common code for GET and HEAD commands.
      
      This sends the response code and MIME headers.
      
      Return value is either a file object (which has to be copied
      to the outputfile by the caller unless the command was HEAD,
      and must be closed by the caller under all circumstances), or
      None, in which case the caller has nothing further to do.
      
      """
      path = self.translate_path(self.path)
      f = None
      if os.path.isdir(path):
        parts = urllib.parse.urlsplit(self.path)
        if not parts.path.endswith('/'):
        # redirect browser - doing basically what apache does
          self.send_response(HTTPStatus.MOVED_PERMANENTLY)
          new_parts = (parts[0], parts[1], parts[2] + '/',
               parts[3], parts[4])
          new_url = urllib.parse.urlunsplit(new_parts)
          self.send_header("Location", new_url)
          self.send_header("Content-Length", "0")
          self.end_headers()
          return None
        for index in "index.html", "index.htm":
          index = os.path.join(path, index)
          if os.path.isfile(index):
            path = index
            break
        else:
          return self.list_directory(path)
      # load pages even the file extension isnt specified
      # this is where this function code was modified
      elif not path.endswith("/"):
        for suffix in ".html", ".htm":
          filename = path + suffix
          if os.path.isfile(filename):
            path = filename
            break
      ctype = self.guess_type(path)
      # check for trailing "/" which should return 404. See Issue17324
      # The test for this was added in test_httpserver.py
      # However, some OS platforms accept a trailingSlash as a filename
      # See discussion on python-dev and Issue34711 regarding
      # parsing and rejection of filenames with a trailing slash
      if path.endswith("/"):
        self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        return None
      try:
        f = open(path, 'rb')
      except OSError:
        self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        return None
      
      try:
        fs = os.fstat(f.fileno())
        # Use browser cache if possible
        if ("If-Modified-Since" in self.headers
          and "If-None-Match" not in self.headers):
          # compare If-Modified-Since and time of last file modification
          try:
            ims = email.utils.parsedate_to_datetime(
            self.headers["If-Modified-Since"])
          except (TypeError, IndexError, OverflowError, ValueError):
            # ignore ill-formed values
            pass
          else:
            if ims.tzinfo is None:
              # obsolete format with no timezone, cf.
              # https://tools.ietf.org/html/rfc7231#section-7.1.1.1
              ims = ims.replace(tzinfo=datetime.timezone.utc)
            if ims.tzinfo is datetime.timezone.utc:
              # compare to UTC datetime of last modification
              last_modif = datetime.datetime.fromtimestamp(
                fs.st_mtime, datetime.timezone.utc)
              # remove microseconds, like in If-Modified-Since
              last_modif = last_modif.replace(microsecond=0)
              
              if last_modif <= ims:
                self.send_response(HTTPStatus.NOT_MODIFIED)
                self.end_headers()
                f.close()
                return None
        
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified",
        self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f
      except:
        f.close()
        raise
    
    def send_error(self, code, message=None, explain=None):
      """Modified function to open 404 page"""
      try:
        shortmsg, longmsg = self.responses[code]
      except KeyError:
        shortmsg, longmsg = '???', '???'
      if message is None:
        message = shortmsg
      if explain is None:
        explain = longmsg
      self.log_error("code %d, message %s", code, message)
      self.send_response(code, message)
      self.send_header('Connection', 'close')
      
      # Message body is omitted for cases described in:
      #  - RFC7230: 3.3. 1xx, 204(No Content), 304(Not Modified)
      #  - RFC7231: 6.3.6. 205(Reset Content)
      body = None
      if (code >= 200 and code not in (HTTPStatus.NO_CONTENT, HTTPStatus.RESET_CONTENT, HTTPStatus.NOT_MODIFIED)):
        # HTML encode to prevent Cross Site Scripting attacks
        # (see bug #1100201)
        
        # This is where the code was modified
        try:
          with open(os.path.join(dest, "404.html"), "r", encoding="utf-8") as f:
            notfound = f.read().encode("UTF-8", "replace")
        except:
          notfound = None
        
        if code != 404 or not notfound:
          content = (self.error_message_format % {
            'code': code,
            'message': html.escape(message, quote=False),
            'explain': html.escape(explain, quote=False)
          })
          body = content.encode('UTF-8', 'replace')
        # Send the appropriate 404 web page to the client in-case it isnt found
        else: body = notfound
          
        self.send_header("Content-Type", self.error_content_type)
        self.send_header('Content-Length', str(len(body)))
      self.end_headers()
      
      if self.command != 'HEAD' and body:
          self.wfile.write(body)
    
    def log_message(self, format, *args):
      message = format % args
      logger.info("server  - [%s] %s", self.address_string(), message.translate(self._control_char_table))
  
  # This class was from the source code of http.server module
  class DualStackServer(ThreadingHTTPServer):
    def server_bind(self):
      # suppress exception when protocol is IPv4
      with contextlib.suppress(Exception):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        return super().server_bind()
    
    def finish_request(self, request, client_address):
      self.RequestHandlerClass(request, client_address, self, directory=dest)
  
  DualStackServer.address_family, type, proto, canonname, sockaddr = next(iter(socket.getaddrinfo(None, serverPort, type=socket.SOCK_STREAM, flags=socket.AI_PASSIVE)))
  
  httpd = DualStackServer(("", serverPort), HTTPRequestHandler)
  host, port = httpd.socket.getsockname()[:2]
  urlhost = f"[{host}]" if ":" in host else host

# Handle threads
if args.watch or args.serve:
  try:
    if args.watch: print("Watch mode started. Press CTRL+C to escape.")
    if args.serve:
      print(f"Running server on {host} port {port} (http://{urlhost}:{port}/) ...")
      httpd.serve_forever()
    else:
      while True: time.sleep(1)
  except KeyboardInterrupt:
    print("\n")
    if args.serve: print("Server stopped...")
    if args.watch: stop_watching()

# Package the output as an archive file
if args.pack:
  import tarfile
  import zipfile
  
  if not os.path.exists(dest): update()
  
  print("Packaging output...")
  
  if os.path.exists(dist): safe_delete(dist)
  os.mkdir(dist)
  
  # open archive streams
  tgzf = tarfile.open(os.path.join(dist, "VYTDocs.tgz"), "w:gz")
  zipf = zipfile.ZipFile(os.path.join(dist, "VYTDocs.zip"), "w", zipfile.ZIP_DEFLATED, compresslevel=9)
  
  # iterate over all files
  for root, dirs, files in os.walk(dest):
    relroot = pathlib.Path(root).relative_to(dest)
    # exclude .github
    if relroot.is_relative_to(".github"): continue
    for file in files:
      # process needed paths
      srcfile = os.path.join(root, file)
      arcname = relroot / file
      # write files
      tgzf.add(srcfile, arcname=arcname)
      zipf.write(srcfile, arcname)
  
  # flush and close (save) archive streams
  tgzf.close()
  zipf.close()
  
  print(f"Distribution packages was saved on {dist} folder.")

# Deploy to GitHub pages
# Note:  If you are a contributor, please dont use this flag else this site will be
# deployed on your personal GitHub pages.
if args.deploy:
  try: from ghp_import import ghp_import
  except ImportError: sys.exit("ghp-import module isn't installed. Did you setup the workspace?")
  
  if not os.path.exists(dest): update()
  
  # add last commit hash that had been deployed like MKDocs do so its easily
  # accessible
  import subprocess
  pipe = subprocess.Popen(["git", "rev-parse", "head"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  sha1 = pipe.communicate()[0].decode()
  pipe.kill()
  msg = "deploy: %s" % (sha1)
  
  print("Deploying to GitHub Pages...")
  
  try:
    ghp_import(dest, mesg=msg, push=True, branch="site")
  except:
    print("Deployment failed.")


# save changes on records
with open(recordsLoc, "w", encoding="utf-8") as f:
  json.dump(records, f, separators=(",",":"))

