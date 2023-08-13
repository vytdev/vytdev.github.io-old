import os
import shutil
import pathlib
import time
import json
import re

# cd to repository root
os.chdir(os.path.normpath(os.path.dirname(__file__)))

# utility function for dumping json with int keys
def stringify(obj):
    if isinstance(obj, dict):
        return "{" + ",".join("%s:%s" % (stringify(k), stringify(v)) for k, v in obj.items()) +"}"
    if isinstance(obj, list):
        return "[" + ",".join(stringify(el) for el in obj) + "]"
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

# a class that handles builds
class Builder:
    def __init__(self, **kwargs):
        # paths to use
        self.docs = pathlib.Path("docs")
        self.src = pathlib.Path("src")
        self.dest = pathlib.Path("dist")
        self.outdir = pathlib.Path("dist/site")
        
        # "path": ident
        self.pages = dict()
        # { ...ident: { ... } }
        self.sitemap = dict()
        
        # excess keywords
        self.config = kwargs
        
        # apply basic config on logger, level to info
        import logging
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
        self.logger = logging.root
        
        # load records
        self.load_records()
    
    def save_records(self):
        with open("records.json", "w", encoding="utf-8") as f:
            json.dump(self.records, f, separators=(",", ":"))
    
    def load_records(self):
        with open("records.json", "r", encoding="utf-8") as f:
            records = json.load(f)
        # make sure these are in records to ensure no errors will occur related on it
        if not "created" in records: records["created"] = {}
        if not "redirects" in records: records["redirects"] = {}
        if not "deletions" in records: records["deletions"] = {}
        self.records = records
    
    def load_templates(self, auto_reload=False):
        """Loads template files"""
        import jinja2
        
        # support resolving urls
        @jinja2.pass_context
        def url_filter(context, value):
            return str(pathlib.PosixPath(os.path.relpath(value, start=context["doc"]["location"])))[3:]
        
        # setup env
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader([
            self.src,
            self.docs
        ]), auto_reload=auto_reload)
        self.env.filters["url"] = url_filter
        
        # base template
        self.base = self.env.get_template("base.tmp.html")
        # sitemap template
        self.sitemap_template = self.env.get_template("sitemap.tmp.xml")
        # redirects template
        self.redirect_template = self.env.get_template("redirect.tmp.html")
        
        # utility function to print sitemap
        def print_sitemap():
            with open(os.path.join(self.outdir, "sitemap.xml"), "w", encoding="utf-8") as f:
                f.write(self.sitemap_template.render(pages=self.sitemap.values()))
        self.print_sitemap = print_sitemap
    
    def load_markdown(self):
        """Load markdown processors"""
        import markdown
        import pygments
        import xml.etree.ElementTree as ET
        
        dest = self.outdir
        
        # load gemoji icon db
        with open("vendor/gemoji.json", "r", encoding="utf-8") as f:
            gemoji = json.load(f)
        
        # :icon: processor
        class IconInlineProcessor(markdown.inlinepatterns.InlineProcessor):
            def __init__(self, *args, **kwargs):
                super().__init__(r":(\w+):", *args, **kwargs)
            
            def handleMatch(self, m, data):
                icon = m.group(1).lower()
                txt = gemoji[icon] if icon in gemoji else m.group(0)
                return txt, m.start(0), m.end(0)
        
        # substitutes html
        class HTMLEntitiesInlineProcessor(markdown.inlinepatterns.InlineProcessor):
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
        class InlineElementProcessor(markdown.inlinepatterns.InlineProcessor):
            def __init__(self, element, idx, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.element = element
                self.idx = idx
            
            def handleMatch(self, m, data):
                el = ET.Element(self.element)
                el.text = m.group(self.idx)
                return el, m.start(0), m.end(0)
        
        # handle strikethrough and sub
        class TildeInlineProcessor(markdown.inlinepatterns.AsteriskProcessor):
            PATTERNS = [
                markdown.inlinepatterns.EmStrongItem(re.compile(r'(~)\1{2}(.+?)\1(.*?)\1{2}', re.DOTALL | re.UNICODE), 'double', 'del,sub'),
                markdown.inlinepatterns.EmStrongItem(re.compile(r'(~)\1{2}(.+?)\1{2}(.*?)\1', re.DOTALL | re.UNICODE), 'double', 'sub,del'),
                markdown.inlinepatterns.EmStrongItem(re.compile(r'(?<!\w)(~)\1(?!\1)(.+?)(?<!\w)\1(?!\1)(.+?)\1{3}(?!\w)', re.DOTALL | re.UNICODE), 'double2', 'del,sub'),
                markdown.inlinepatterns.EmStrongItem(re.compile(r'(?<!\w)(~{2})(?!~)(.+?)(?<!~)\1(?!\w)', re.DOTALL | re.UNICODE), 'single', 'del'),
                markdown.inlinepatterns.EmStrongItem(re.compile(r'(~)(?!~)(.+?)(?<!~)\1', re.DOTALL | re.UNICODE), 'single', 'sub')
            ]
        
        # create task lists like on GitHub Flavored Markdown
        class TaskListBlockProcessor(markdown.blockprocessors.BlockProcessor):
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
        class SnippetsBlockProcessor(markdown.blockprocessors.BlockProcessor):
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
                        lexer = pygments.lexers.get_lexer_for_filename(filename)
                    except:
                        lexer = pygments.lexers.get_lexer_by_name("text")
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
                            lexer = pygments.lexers.get_lexer_for_mimetype(content_type["mimetype"])
                        except:
                            lexer = pygments.lexers.get_lexer_by_name("text")
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
                formatter = pygments.formatters.HtmlFormatter(cssclass="snippet", wrapcode=True, linenos=True, linenostart=start + 1)
                result = pygments.highlight(snippet, lexer, formatter)
                
                # put the snippet to tree
                div = ET.SubElement(parent, "div")
                div.set("class", "external-snippet")
                div.set("data-path", match.group(1))
                div.set("data-filename", filename)
                div.text = self.md.htmlStash.store(result)
            
        class TableWrapper(markdown.treeprocessors.Treeprocessor):
            def run(self, root):
                for idx, val in enumerate(root):
                    if val.tag != "table" or val.get("class") == "snippettable": continue
                    root.remove(val)
                    wrapper = ET.Element("div")
                    wrapper.set("class", "table")
                    wrapper.append(val)
                    root.insert(idx, wrapper)
        
        class CustomExtension(markdown.extensions.Extension):
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
                # table block processors
                md.treeprocessors.register(TableWrapper(md), 'tablewrapper', 0)
            
            def reset(self):
                self.md.current_loc = None
        
        self.md = markdown.Markdown(extensions=[CustomExtension(), "extra", "admonition", "toc", "meta", "sane_lists", "wikilinks", "codehilite", "smarty"], extension_configs={
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
                "css_class": "snippet",
                "linenums": False
            }
        })
    
    def load_indexer(self):
        import unicodedata
        self.data = {
            # pageid: { ... }
            "pages": dict(),
            # "word": wordID
            "words": dict(),
            # wordID: [...pageid]
            "index": dict(),
            # pageid: {wordID: count}
            "count": dict(),
            # number of words in all pages
            "terms": 0,
            # number of total pages
            "files": 0,
        }
        
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
        
        stemmer = PorterStemmer()
        
        # objects needed for indexing
        punct = re.compile("[\\s~`’‘|^°{}[\\]()<>\\\\%@#$&\\-+=/*\"':;!?.,]+")
        # contractions
        contractions = [
            (re.compile(r"n't\b"), ' not '),
            (re.compile(r"can't\b"), 'can not '),
            (re.compile(r"'ll\b"), ' will '),
            (re.compile(r"'s\b"), ' is '),
            (re.compile(r"'re\b"), ' are '),
            (re.compile(r"'ve\b"), ' have '),
            (re.compile(r"'m\b"), ' am '),
            (re.compile(r"'d\b"), ' had '),
            # full-word
            (re.compile(r"\bcannot\b"), 'can not'),
            (re.compile(r"\bgonna\b"), 'going to'),
            (re.compile(r"\bwanna\b"), 'want to')
        ]
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
        metare = re.compile( # regex for removing metadata in markdown files
            r"^-{3}?(\s.*)?" # begin
            r"(\n[ ]{0,3}[A-Za-z0-9_-]+:\s*.*" # meta
            r"(\n[ ]{4,}.*)*?)*" # more
            r"\n(\n|(-{3}|\.{3})(\s.*)?)" # end
        , flags=re.M)
        
        # removes a page in current index
        def remove_index(ident):
            self.data["files"] -= 1
            content = self.data["count"][ident]
            for wordID in content:
                if wordID == "num":
                    continue
                self.data["index"][wordID].remove(ident)
            self.data["terms"] -= content["num"]
            del self.data["pages"][ident]
            del self.data["count"][ident]
        self.remove_index = remove_index
        
        # builds page index
        def index_page(ident, content):
            if ident in self.data["count"]:
                remove_index(ident)
            # number of repititions of terms in pages
            termsrep = dict() # wordID: count
            
            # remove metadata
            raw = metare.sub("", content)
            # normalize content
            raw = unicodedata.normalize("NFD", raw)
            # lowercase
            raw = raw.lower()
            # expand contractions
            for regex, repl in contractions:
                raw = regex.sub(repl, raw)
            # split into tokens
            tokens = punct.split(raw)
            # strip whitespace on tokens
            tokens = (token.strip() for token in tokens)
            # filter tokens by length and stopwords
            tokens = (token for token in tokens if token and token not in stopwords)
            # stem tokens
            tokens = (stemmer.stem(token, 0, len(token) - 1) for token in tokens)
            # found (can be multiple) terms
            terms = []
            # number of words found in the page
            docwords = 0
            # store to index
            for token in tokens:
                # token not indexed
                if not token in self.data["words"]:
                    wordID = len(self.data["words"])
                    self.data["words"][token] = wordID
                    self.data["index"][wordID] = []
                # id of the token
                wordID = self.data["words"][token]
                # store num of docs containing the term
                if not token in terms:
                    self.data["index"][wordID] = self.data["index"].get(wordID, [])
                    self.data["index"][wordID].append(ident)
                    terms.append(token)
                termsrep[wordID] = termsrep.get(wordID, 0) + 1
                docwords += 1
            self.data["terms"] += docwords
            
            termsrep["num"] = docwords
            
            self.data["count"][ident] = termsrep
            
            self.data["files"] += 1
            
            # return page index data
            return termsrep
        self.index_page = index_page
        
        def print_index():
            with open(self.outdir / "index.js", "w", encoding="utf-8") as f:
                f.write("window.searchIndex=" + stringify(self.data))
        self.print_index = print_index
    
    def load_watcher(self):
        from watchdog import events as watchdogEvents, observers as watchdogObservers
        
        watchers = []
        
        builder = self
        
        class Watcher(watchdogEvents.FileSystemEventHandler):
            def __init__(self, indir, outdir, debug=False):
                self.indir = indir
                self.outdir = outdir
                self.debug = debug
                self.observer = watchdogObservers.Observer()
                self.observer.schedule(self, path=indir, recursive=True)
                watchers.append(self)
            
            def start(self):
                self.observer.start()
            
            def stop(self):
                self.observer.stop()
                self.observer.join()
                watchers.remove(self)
            
            def on_any_event(self, ev):
                """Handle all event types"""
                # report any events
                if self.debug:
                    what = "directory" if ev.is_directory else "file"
                    msg = "Unknown event!"
                if ev.event_type == watchdogEvents.EVENT_TYPE_MOVED: msg = "Moved %s: from %s to %s" % (what, ev.src_path, ev.dest_path)
                elif ev.event_type == watchdogEvents.EVENT_TYPE_CREATED: msg = "Created %s: %s" % (what, ev.src_path)
                elif ev.event_type == watchdogEvents.EVENT_TYPE_MODIFIED: msg = "Modified %s: %s" % (what, ev.src_path)
                elif ev.event_type == watchdogEvents.EVENT_TYPE_DELETED: msg = "Deleted %s: %s" % (what, ev.src_path)
                # only necessary events
                if not ev.event_type == watchdogEvents.EVENT_TYPE_OPENED and not ev.event_type == watchdogEvents.EVENT_TYPE_CLOSED:
                    builder.logger.info("watcher - %s", msg)
                # update paths
                ev.from_path = pathlib.Path(ev._src_path).relative_to(self.indir)
                if ev.event_type == watchdogEvents.EVENT_TYPE_MOVED: ev.to_path = pathlib.Path(ev._dest_path).relative_to(self.indir)
            
            def on_moved(self, ev):
                shutil.move(self.outdir / ev.from_path, self.outdir / ev.to_path)
            
            def on_created(self, ev):
                if ev.is_directory: os.makedirs(self.outdir / ev.from_path)
                else: shutil.copyfile(self.indir / ev.from_path, self.outdir / ev.from_path)
            
            def on_modified(self, ev):
                if not ev.is_directory: self.on_created(ev)
            
            def on_deleted(self, ev):
                builder.delete_path(self.outdir / ev.from_path)
        
        self.Watcher = Watcher
        
        def stop_watching():
            for watcher in watchers:
                watcher.stop()
            print("Watch mode stopped.")
        self.stop_watching = stop_watching
    
    def load_server(self):
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
        
        builder = self
        
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
                        with open(os.path.join(builder.outdir, "404.html"), "r", encoding="utf-8") as f:
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
                builder.logger.info("server  - [%s] %s", self.address_string(), message.translate(self._control_char_table))
        
        # This class was from the source code of http.server module
        class DualStackServer(ThreadingHTTPServer):
            def server_bind(self):
                # suppress exception when protocol is IPv4
                with contextlib.suppress(Exception):
                    self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                    return super().server_bind()
            
            def finish_request(self, request, client_address):
                self.RequestHandlerClass(request, client_address, self, directory=builder.outdir)
        
        self.HTTPRequestHandler = HTTPRequestHandler
        self.DualStackServer = DualStackServer
    
    def package(self):
        import tarfile
        import zipfile
        
        # open archive streams
        tgzf = tarfile.open(os.path.join(self.dest, "VYTDocs.tgz"), "w:gz")
        zipf = zipfile.ZipFile(os.path.join(self.dest, "VYTDocs.zip"), "w", zipfile.ZIP_DEFLATED, compresslevel=9)
        
        # iterate over all files
        for root, dirs, files in os.walk(self.outdir):
            relroot = pathlib.Path(root).relative_to(self.outdir)
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
    
    def deploy(self):
        """Deploy to GitHub Pages"""
        try: from ghp_import import ghp_import
        except ImportError: exit("ghp-import module isn't installed. Did you setup the workspace?")
        
        if input("Are you sure you want to deploy this site? [y/n]: ").lower() != "y":
            return
        
        # add last commit hash that had been deployed like MKDocs do so its easily
        # accessible
        import subprocess
        pipe = subprocess.Popen(["git", "rev-parse", "head"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sha1 = pipe.communicate()[0].decode()
        pipe.kill()
        msg = "deploy: %s" % (sha1)
        
        print("Deploying to GitHub Pages...")
        
        try:
            ghp_import(self.outdir, mesg=msg, push=True, branch="site")
        except:
            print("Deployment failed.")
    
    def build_page(self, path, index=False):
        path = os.path.normpath(path)
        ident = self.pages.get(path)
        if not ident:
            ident = len(self.pages)
            self.pages[path] = ident
        
        path = pathlib.Path(path)
        rel = path.relative_to(self.docs)
        dest = self.outdir / rel.parent / (rel.stem + ".html")
        tmpl = rel.parent / (rel.stem + rel.suffix + ".tmp.html")
        loc = str(rel.parent / rel.stem)
        self.md.current_loc = rel
        
        template = self.base
        if os.path.exists(self.src / tmpl) or os.path.exists(self.docs / tmpl):
            template = self.env.get_template(str(tmpl))
        else:
            for parent in rel.parents:
                tmplloc = parent / "template.tmp.html"
                if os.path.exists(self.src / tmplloc) or os.path.exists(self.docs / tmplloc):
                    template = self.env.get_template(str(tmplloc))
                    break
        
        # get creation time
        if not loc in self.records["created"]:
            creation = self.records["created"][loc] = time.time()
        else:
            creation = self.records["created"][loc]
        
        # open file
        with open(path, "r", encoding="utf-8") as f:
            md = f.read()
        # convert html
        html = self.md.convert(md)
        
        contributorRE = re.compile(r"^([^\<]+)(\s+?\<([^\>]+)\>)?$")
        contributors = []
        if "contributors" in self.md.Meta:
            for person in self.md.Meta["contributors"]:
                match = contributorRE.match(person)
                contributors.append({
                    "name": match.group(1),
                    "url": match.group(3)
                })
        
        keywords = []
        if "keywords" in self.md.Meta:
            for line in self.md.Meta["keywords"]:
                keywords += line.split(", ")
        
        # index page
        if index:
            self.index_page(ident, md)
            if self.config.get("watch"):
                # update the index, may cause the builder to slow, but can help when debugging
                self.print_index()
        
        timeformat = "%A, %B %d %Y"
        created = time.strftime(timeformat, time.gmtime(creation))
        updated = time.strftime(timeformat, time.strptime(self.md.Meta["updated"][0], "%d-%m-%Y") if "updated" in self.md.Meta else time.gmtime(creation))
        
        ctx = {
            "title": self.md.Meta.get("title", ["Untitled"])[0],
            "about": self.md.Meta.get("about", ["No description"])[0],
            "prev": self.md.Meta.get("prev", [None])[0],
            "next": self.md.Meta.get("next", [None])[0],
            "contributors": contributors,
            "keywords": keywords,
            "contents": remap_toc(self.md.toc_tokens),
            "home": rel.stem == "index",
            "location": loc,
            "created": created,
            "updated": updated,
        }
        ctx["canonical"] = "https://vytdev.github.io/" + ctx["location"]
        
        # set this page on sitemap
        self.sitemap[ident] = {
            "location": ctx["canonical"],
            "lastmod": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.strptime(updated, timeformat))
        }
        # update sitemap if in watchmode
        if self.config.get("watch"):
            self.print_sitemap()
        
        seo = json.dumps({
            "@context": "https://schema.org",
            "@type":  "WebSite" if ctx["home"] and len(rel.parents) == 2 else "WebPage",
            "description": ctx["about"],
            "headline": ctx["title"],
            "name": ctx["title"],
            "url": ctx["canonical"],
        }, separators=(",",":"))
        
        self.data["pages"][ident] = ctx
        
        with open(dest, "w", encoding="utf-8") as f:
            f.write(template.render(doc=ctx, config=self.config, toc=self.md.toc, content=html, seo=seo, meta=stringify(ctx)))
    
    def create_redirects(self):
        """Create redirects for moved files"""
        for src, dest in self.records["redirects"].items():
            with open(os.path.join(self.outdir, src + ".html"), "w", encoding="utf-8") as f:
                f.write(self.redirect_template.render(location=str(pathlib.PosixPath(dest))))
    
    def build(self):
        """Build the site"""
        # copy res
        for root, dirs, files in os.walk(self.src):
            root = pathlib.Path(root)
            relroot = root.relative_to(self.src)
            
            dest = self.outdir / relroot
            self.makedir(dest)
            
            for file in files:
                if not ".tmp." in file:
                    shutil.copyfile(root / file, dest / file)
        # process pages
        for root, dirs, files in os.walk(self.docs):
            root = pathlib.Path(root)
            relroot = root.relative_to(self.docs)
            
            self.makedir(self.outdir / relroot)
            
            for file in files:
                if not file.endswith(".md"):
                    if not ".tmp." in file:
                        shutil.copyfile(root / file, os.path.join(self.outdir, file))
                    continue
                self.build_page(root / file, True)
        
        # create redirects
        self.create_redirects()
        # create sitemap
        self.print_sitemap()
    
    def delete_path(self, path):
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.unlink(path)
            return True
        return False
    
    def makedir(self, path):
        if os.path.exists(path) and os.path.isfile(path):
            os.unlink(path)
        if not os.path.exists(path):
            os.makedirs(path)
            return True
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Website toolkit.")
    parser.add_argument("--build", "-b", action="store_true", help="Build the site")
    parser.add_argument("--clean", "-c", action="store_true", help="Clean the workspace")
    parser.add_argument("--debug", "-t", action="store_true", help="Build in debug mode (enables eruda console)")
    parser.add_argument("--watch", "-w", action="store_true", help="Enable watch mode")
    parser.add_argument("--serve", "-s", action="store_true", help="Run localhost server")
    parser.add_argument("--pack", "-p", action="store_true", help="Package distribution files")
    parser.add_argument("--deploy", "-d", action="store_true", help="Deploy to GitHub Pages")
    args = parser.parse_args()
    
    ctx = Builder(debug=args.debug, watch=args.watch)
    
    built = False
    loaded = False
    
    def load():
        global loaded
        if not loaded:
            ctx.load_templates(auto_reload=args.watch)
            ctx.load_markdown()
            ctx.load_indexer()
            loaded = True
    
    def build():
        if not loaded:
            load()
        if not built:
            ctx.build()
            ctx.print_index()
    
    if args.clean:
        print("Cleaning workspace...")
        ctx.delete_path(ctx.outdir)
        ctx.delete_path(ctx.dest)
        print("Workspace cleaned")
    
    if args.build:
        print("Building pages...")
        start = time.monotonic()
        build()
        delta = time.monotonic() - start
        print("Built pages. Elapsed time %.3f secs" % (delta))
    
    if args.watch:
        load()
        if not os.path.exists(ctx.dest): build()
        
        ctx.load_watcher()
        
        # observer for docs folder (builds pages)
        class DocWatcher(ctx.Watcher):
            def on_moved(self, ev):
                if ev.is_directory:
                    shutil.move(self.outdir / ev.from_path, self.outdir / ev.to_path)
                else:
                    src = self.outdir / ev.from_path.parent / (ev.from_path.stem + ".html")
                    dest = self.outdir / ev.to_path.parent / (ev.to_path.stem + ".html")
                    if ev.from_path.suffix == ".md":
                        pathname = str(src)
                        if ev.to_path.suffix == ".md":
                            ctx.pages[str(dest)] = ctx.pages[pathname]
                            shutil.move(src, dest)
                        else:
                            os.unlink(src)
                            shutil.copyfile(self.indir / ev.to_path, self.outdir / ev.to_path)
                        del ctx.pages[pathname]
                    elif ev.to_path.suffix == ".md":
                        os.unlink(self.outdir / ev.from_path)
                        ctx.build_page(self.indir / ev.to_path, index=True)
                    elif not ".tmp" in ev.to_path.suffixes:
                        ctx.delete_path(self.outdir / ev.from_path)
                        shutil.copyfile(self.indir / ev.to_path, self.outdir / ev.to_path)
            
            def on_modified(self, ev):
                if not ev.is_directory:
                    if ev.from_path.suffix == ".md":
                        ctx.build_page(self.indir / ev.from_path, index=True)
                    elif not ".tmp" in ev.from_path.suffixes:
                        shutil.copyfile(self.indir / ev.from_path, self.outdir / ev.from_path)
            
            def on_created(self, ev):
                if ev.is_directory:
                    ctx.makedir(self.outdir / ev.from_path)
                elif ev.from_path.suffix == ".md":
                    ctx.build_page(self.indir / ev.from_path, index=True)
                elif not ".tmp" in ev.from_path.suffixes:
                    shutil.copyfile(self.indir / ev.from_path, self.outdir / ev.from_path)
            
            def on_deleted(self, ev):
                if not ev.is_directory and ev.from_path.suffix == ".md":
                    ctx.delete_path(self.outdir / ev.from_path.parent / (ev.from_path.stem + ".html"))
                else:
                    ctx.delete_path(self.outdir / ev.from_path)
        
        # observer for src folder (excludes template files)
        class SrcWatcher(ctx.Watcher):
            def on_moved(self, ev):
                if ev.is_directory:
                    shutil.move(self.outdir / ev.from_path, self.outdir / ev.to_path)
                elif not ".tmp" in ev.to_path.suffixes:
                    ctx.delete_path(self.outdir / ev.from_path)
                    shutil.copyfile(self.indir / ev.to_path, self.outdir / ev.to_path)
            
            def on_modified(self, ev):
                if not ev.is_directory and not ".tmp" in ev.from_path.suffixes:
                    shutil.copyfile(self.indir / ev.from_path, self.outdir / ev.from_path)
            
            def on_created(self, ev):
                if ev.is_directory:
                    ctx.makedir(self.outdir / ev.from_path)
                elif not ".tmp" in ev.from_path.suffixes:
                    shutil.copyfile(self.indir / ev.from_path, self.outdir / ev.from_path)
        
        DocWatcher(ctx.docs, ctx.outdir, debug=True).start()
        SrcWatcher(ctx.src, ctx.outdir, debug=True).start()
    
    if args.serve:
        import socket
        ctx.load_server()
        
        load()
        if not os.path.exists(ctx.dest): build()
        
        serverPort = 24580
        
        ctx.DualStackServer.address_family, type, proto, canonname, sockaddr = next(iter(socket.getaddrinfo(None, serverPort, type=socket.SOCK_STREAM, flags=socket.AI_PASSIVE)))
        
        httpd = ctx.DualStackServer(("", serverPort), ctx.HTTPRequestHandler)
        host, port = httpd.socket.getsockname()[:2]
        urlhost = f"[{host}]" if ":" in host else host
    
    # handle threads
    if args.serve or args.watch:
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
            if args.watch: ctx.stop_watching()
    
    if args.pack:
        print("Packaging output...")
        
        if not os.path.exists(ctx.dest): build()
        
        ctx.package()
        print(f"Distribution files was saved on '{ctx.dest}' folder")
    
    if args.deploy:
        if not os.path.exists(ctx.outdir): build()
        
        ctx.deploy()
    
    ctx.save_records()
