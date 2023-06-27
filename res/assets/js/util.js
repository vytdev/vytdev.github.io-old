/*!
 * util.js — Doc resource
 */
var doc = (function(factory) {
  "use strict";
  // expose this to global scope
  var out;
  if (typeof window != "undefined" && window.window == window) out = factory(window);
  else if (typeof self == "object" && self.self == self) out = factory(self);
  else if (typeof global != "undefined") out = factory(global);
  else out = factory(this);
  
  if (typeof define == "function" && define.amd) define("util", [], function() { return out });
  if (typeof module == "object" && typeof exports == "object") module.exports = out;
  
  return out
})(function factory(scope) {
"use strict";

var doc = scope.doc = {},
    version = doc.version = "0.2.1";

// short names of common functions for faster retrival
var hasProp = Function.prototype.call.bind(Object.prototype.hasOwnProperty);

if (!hasProp(window, "jQuery")) throw "jQuery not found!"

var _document = $(document),
    _window = $(window);

var rwhitespace = /\s+/g,
    rurlquerydecode = /\+/g;

if (typeof RegExp.escape != "function") {
  var escapeRegEx = /[\[\](){}<>|\\$^\-?.*+=]/g;
  RegExp.escape = function(obj) {
    if (typeof obj == "string") return obj.replace(escapeRegEx, "\\$&");
    throw "RegExp.escape: Parameter must be a String!";
  }
}

// add queries
doc.query = (function(){
  var query = document.location.search;
  var parts = query.slice(query.indexOf("?") + 1).split("&");
  var output = {};
  var i, sepidx, part, key, val;
  for (i = 0; i < parts.length; i++) {
    part = parts[i];
    sepidx = part.indexOf("=");
    key = decodeURIComponent((sepidx == -1 ? part : part.substr(0, sepidx)).replace(rurlquerydecode, " "));
    val = decodeURIComponent((sepidx == -1 ? part : part.substr(sepidx + 1, part.length)).replace(rurlquerydecode, " "));
    if (hasProp(output, key)) output[key].push(val);
    else output[key] = [val];
  };
  return output;
})();


// highlights text on the doc (keeps the markup intact)
var highlightSkipTags = ["BUTTON","SELECT","TEXTAREA"],
    highlightClass = "highlight",
    noHighlightClass = "nohighlight";
doc.highlight = function(text, node) {
  if (!node) node = document.body;
  if (typeof text != "string") throw "doc.highlight first argument 'text' must be a string!"
  var a = text.toLowerCase().split(rwhitespace); // highlight multiple words
  if (node.nodeType == document.TEXT_NODE) {
    if (node.parentNode.classList.contains(noHighlightClass) || node.parentNode.classList.contains(highlightClass)) return;
    var i, t, p, s, l, v, c = node.nodeValue;
    v = c.toLowerCase(); // lower case for finding indexes
    for (i = 0; i < a.length; i++) {
      t = a[i];
      p = v.indexOf(t); // find text
      if (p < 0) continue;
      l = t.length;
      s = document.createElement("span");
      s.className = highlightClass;
      s.appendChild(document.createTextNode(c.substr(p, l)));
      node.parentNode.insertBefore(s, node.parentNode.insertBefore(document.createTextNode(c.substr(p + l)), node.nextSibling));
      node.nodeValue = c.substr(0, p);
    }
  }
  else if (!highlightSkipTags.includes(node.tagName)) {
    var i, n;
    for (i = 0; i < node.childNodes.length; i++) {
      n = node.childNodes[i];
      if (n.tagName !== "SVG") doc.highlight(text, n);
    }
  }
}

// remove the current highlights on document
doc.unhighlight = function(node) {
  if (!node) node = document.body;
  if (node.tagName == "SPAN" && node.className == highlightClass) {
    var p = node.previousSibling,
        n = node.nextSibling,
        r = node.parentNode,
        t = "", b = node;
    if (p && p.nodeType == document.TEXT_NODE) {
      b = p;
      t += p.nodeValue;
    }
    t += node.childNodes[0].nodeValue;
    if (n && n.nodeType == document.TEXT_NODE) {
      r.removeChild(n);
      t += n.nodeValue;
    }
    r.insertBefore(document.createTextNode(t), b);
    r.removeChild(node);
    if (p) r.removeChild(p);
  }
  else if (node.nodeType != document.TEXT_NODE) {
    var i, n, m, l = node.childNodes.length;
    for (i = 0; i < l; i++) {
      n = node.childNodes[i];
      if (n.nodeType == document.ELEMENT_NODE) doc.unhighlight(n);
      m = node.childNodes.length;
      if (l != m) {
        l = m;
        i = 0;
      }
    }
  }
}

// simple toast api
var queuedToasts = [];

doc.toast = function(msg) {
  queuedToasts.push(msg);
  doc.dispatchEvent("toastQueued", msg);
  return msg;
}

// ISO-639-1 language codes and names
var langs = {"ab":"Abkhazian","aa":"Afar","af":"Afrikaans","ak":"Akan","sq":"Albanian","am":"Amharic","ar":"Arabic","an":"Aragonese","hy":"Armenian","as":"Assamese","av":"Avaric","ae":"Avestan","ay":"Aymara","az":"Azerbaijani","bm":"Bambara","ba":"Bashkir","eu":"Basque","be":"Belarusian","bn":"Bengali","bh":"Bihari languages","bi":"Bislama","bs":"Bosnian","br":"Breton","bg":"Bulgarian","my":"Burmese","ca":"Catalan, Valencian","km":"Central Khmer","ch":"Chamorro","ce":"Chechen","ny":"Chichewa, Chewa, Nyanja","zh":"Chinese","cu":"Church Slavonic, Old Bulgarian, Old Church Slavonic","cv":"Chuvash","kw":"Cornish","co":"Corsican","cr":"Cree","hr":"Croatian","cs":"Czech","da":"Danish","dv":"Divehi, Dhivehi, Maldivian","nl":"Dutch, Flemish","dz":"Dzongkha","en":"English","eo":"Esperanto","et":"Estonian","ee":"Ewe","fo":"Faroese","fj":"Fijian","fi":"Finnish","fr":"French","ff":"Fulah","gd":"Gaelic, Scottish Gaelic","gl":"Galician","lg":"Ganda","ka":"Georgian","de":"German","ki":"Gikuyu, Kikuyu","el":"Greek (Modern)","kl":"Greenlandic, Kalaallisut","gn":"Guarani","gu":"Gujarati","ht":"Haitian, Haitian Creole","ha":"Hausa","he":"Hebrew","hz":"Herero","hi":"Hindi","ho":"Hiri Motu","hu":"Hungarian","is":"Icelandic","io":"Ido","ig":"Igbo","id":"Indonesian","ia":"Interlingua (International Auxiliary Language Association)","ie":"Interlingue","iu":"Inuktitut","ik":"Inupiaq","ga":"Irish","it":"Italian","ja":"Japanese","jv":"Javanese","kn":"Kannada","kr":"Kanuri","ks":"Kashmiri","kk":"Kazakh","rw":"Kinyarwanda","kv":"Komi","kg":"Kongo","ko":"Korean","kj":"Kwanyama, Kuanyama","ku":"Kurdish","ky":"Kyrgyz","lo":"Lao","la":"Latin","lv":"Latvian","lb":"Letzeburgesch, Luxembourgish","li":"Limburgish, Limburgan, Limburger","ln":"Lingala","lt":"Lithuanian","lu":"Luba-Katanga","mk":"Macedonian","mg":"Malagasy","ms":"Malay","ml":"Malayalam","mt":"Maltese","gv":"Manx","mi":"Maori","mr":"Marathi","mh":"Marshallese","ro":"Moldovan, Moldavian, Romanian","mn":"Mongolian","na":"Nauru","nv":"Navajo, Navaho","nd":"Northern Ndebele","ng":"Ndonga","ne":"Nepali","se":"Northern Sami","no":"Norwegian","nb":"Norwegian Bokmål","nn":"Norwegian Nynorsk","ii":"Nuosu, Sichuan Yi","oc":"Occitan (post 1500)","oj":"Ojibwa","or":"Oriya","om":"Oromo","os":"Ossetian, Ossetic","pi":"Pali","pa":"Panjabi, Punjabi","ps":"Pashto, Pushto","fa":"Persian","pl":"Polish","pt":"Portuguese","qu":"Quechua","rm":"Romansh","rn":"Rundi","ru":"Russian","sm":"Samoan","sg":"Sango","sa":"Sanskrit","sc":"Sardinian","sr":"Serbian","sn":"Shona","sd":"Sindhi","si":"Sinhala, Sinhalese","sk":"Slovak","sl":"Slovenian","so":"Somali","st":"Sotho, Southern","nr":"South Ndebele","es":"Spanish, Castilian","su":"Sundanese","sw":"Swahili","ss":"Swati","sv":"Swedish","tl":"Tagalog","ty":"Tahitian","tg":"Tajik","ta":"Tamil","tt":"Tatar","te":"Telugu","th":"Thai","bo":"Tibetan","ti":"Tigrinya","to":"Tonga (Tonga Islands)","ts":"Tsonga","tn":"Tswana","tr":"Turkish","tk":"Turkmen","tw":"Twi","ug":"Uighur, Uyghur","uk":"Ukrainian","ur":"Urdu","uz":"Uzbek","ve":"Venda","vi":"Vietnamese","vo":"Volap_k","wa":"Walloon","cy":"Welsh","fy":"Western Frisian","wo":"Wolof","xh":"Xhosa","yi":"Yiddish","yo":"Yoruba","za":"Zhuang, Chuang","zu":"Zulu"};

// Full-text search engine
// using Okapi BM25 algorithm (https://en.m.wikipedia.org/wiki/Okapi_BM25)
doc.search = function (terms, opts) {
  // check index
  if (!index) throw "Index aren't loaded!";
  
  // check arguments
  if (typeof terms != "string") throw "search requires 1 argument with the first argument as a string!";
  
  // process search options
  if (typeof opts != "object") opts = {};
  for (var k in doc.search.config) if (!hasProp(opts, k)) opts[k] = doc.search.config[k];
  
  // verify the language
  if (!hasProp(langs, opts.lang)) throw "Invalid ISO language!";
  if (!hasProp(doc.langdata, opts.lang)) throw "Language '" + opts.lang + "' does not exists!"
  
  var // declare variables
      
      // constants fasten the function
      brem = 1 - opts.b,
      avgdl = index.vocabulary.count / index.docfiles.length,
      k1p = opts.k1 + 1,
      k2p = opts.k2 + 1,
      onhf = 0.5,
      
      // language processor of the queries
      extractor = doc.langdata[opts.lang].split,
      stemmer = doc.langdata[opts.lang].stem,
      stopword = doc.langdata[opts.lang].stop,
      
      // cache objects for searching
      qrl = {}, // collection of real terms before stemming
      qrc = {}, // counts of repititions of each term in the query (before stemming)
      qfc = {}, // counts of repititions of each term in the query (after stemming)
      qtc = 0, // total count of [stemmed] terms (length of qfc)
      qdx = {}, // enum of recorded terms and its index on the record
      zidx = {}, // calculated from query term frequencies
      idf = {}, // collections of idf
      N = index.docfiles.length, // total number of docs indexed
      
      // stores results
      result = [],
      
      // store data for document relevance probobilities (affects idf)
      //postv = {}, // positive probobility (relevant)
      //negtv = {}, // negative probobility (irrelevant)
      R = 0, // count of relevant documents
      r = {}, // collection of count of relevant documents containing each query
      
      // other vars (we need to declare it first to speed up the function)
      l, t, u, qi, qx, tf, m, tc, di, dt, dx, itm, src, K, x, y, z, ri, dfi, D;
  
  // pre-process
  
  // split terms (normalize and tokenize)
  terms = extractor(terms);
  
  // stem and skip stopwords
  l = terms.length;
  for (qi = 0; qi < l; qi++) {
    u = terms[qi]; // the unprocessed query
    if (stopword(u)) continue; // check if it is a stopword
    t = stemmer(u); // processed term
    // record query term
    if (!hasProp(qdx, t)) {
      qx = qtc++; // new query idx
      qdx[qdx[qx] = t] = qx; // insert to records
      qfc[qx] = 0; // add count record
    }
    qx = qdx[t];
    qfc[qx]++; // add 1 to term count record
    qrl[u] = qx; // record raw term stem idx
    qrc[u] = (qrc[u] || 0) + 1; // count raw term duplicates
  }
  
  // add tf and zidx record on queries
  for (qi = 0; qi < qtc; qi++) {
    tf = qfc[qi] / qtc; // current term frequency were calculating
    zidx[qi] = (k2p * tf) / (tf + opts.k2); // new z record for scoring (see later)
  }
  
  // search on all documents
  for (di = 0; di < N; di++) {
    src = index.docfiles[di];
    
    // result item
    itm = {
      relevance: 0,
      path: src.location,
      title: src.title,
      matches: 0,
      words: {},
      ref: di
    };
    
    // match and create result summary
    m = false;
    for (dx in src.terms) {
      dt = index.vocabulary[dx];
      for (qx in qrl) {
        if (typeof qx != "string") continue;
        qi = qrl[qx];
        t = qdx[qi];
        if (dt == t) {
          tc = qrc[qx] * src.terms[index.termidx[t]];
          itm.words[qx] = (itm.words[qx] || 0) + tc;
          itm.matches += tc;
          m = true;
          break;
        }
      }
    }
    
    // if matched ...
    if (m) {
      // calculate the score of this result using our ranking function
      D = src.terms.count; // total count of terms of the document
      K = opts.k1 * (brem + opts.b * (D / avgdl)); // term frequency saturation point
      for (qi = 0; qi < qtc; qi++) {
        qx = index.termidx[qdx[qi]];
        dfi = index.termdoc[qx] || 0; // number of docs containing the term
        ri = r[qi] || 0; // number of relevant docs containing the query qdx[qi]
        tf = (src.terms[qx] || 0) / D; // term frequency
        x = idf[qi] || (idf[qi] = Math.log((((ri + onhf) / (R - ri + onhf)) / ((dfi - ri + onhf) / (N - R - dfi + ri + onhf))) + 1)); // inverse document frequency
        y = (k1p * tf) / (tf + K); // doc terms
        z = zidx[qi]; // query terms
        itm.relevance += x * y * z; // the relevance of the term on the matched document
      }
      // append new result item
      result[result.length] = itm;
    }
  }
  
  // post-process
  
  // sort results
  result.sort(typeof opts.sort == "function" && opts.sort.length == 2 ? opts.sort : typeof opts.sort == "string" ? doc.search.sorters[opts.sort] : doc.search.sorters.relevance);
  
  // final output
  return result;
}

// sorts search results
doc.search.sorters = {};
doc.search.sorters.alphabet = function (a, b) {
  if (a.title < b.title) return 1;
  return -1;
};

doc.search.sorters.relevance = function (a, b) {
  if (a.relevance < b.relevance) return 1;
  else if (a.relevance > b.relevance) return -1;
  else return doc.search.sorters.alphabet(a, b);
};

// index
var index;
Object.defineProperty(doc, "index", {
  get: function() {
    return index;
  },
  set: function(i) {
    var x;
    i.termidx = {};
    for (x = 0; x < i.vocabulary.length; x++)
      i.termidx[i.vocabulary[x]] = x;
    index = i;
    doc.dispatchEvent("searchReady", [index]);
  }
});

Object.defineProperty(doc.search, "ready", {
  get: function() {
    return typeof index != "undefined";
  },
  set: function(v) {
    throw "Property 'ready' is read-only"
  }
})


// configurations in search
doc.search.config = {
  // default language processor (iso)
  lang: "en",
  
  // default sort function for sorting results
  sort: "relevance",
  
  // Okapi BM25 search algorithm free parameters
  k1: 1.2, // scale of how the tf component of the term weight changes as term frequency increases
  k2: 100, // same as k1 but intended for query
  b: 0.75 // regulates the impact of length normalization
};

// object containing language data and processors
doc.langdata = {};

doc.langdata["en"] = (function() {
  // this language data is from modified excerpt of the following:
  // - https://github.com/axa-group/nlp.js
  // - https://www.tartarus.org/~martin/PorterStemmer
  var langEn = {}, // language data
      // used in normalization
      codePoints = /[\u0300-\u036f]/g,
      form = "NFD", // canonical decomposition
      punctuations = /[\s~`’‘|^°{}[\]()<>\\%@#$&\-+=/*"':;!?.,]+/,
      replacements = [ // for quoted contractions
        [/n't([ ,:;.!?]|$)/gi, ' not '],
        [/can't([ ,:;.!?]|$)/gi, 'can not '],
        [/'ll([ ,:;.!?]|$)/gi, ' will '],
        [/'s([ ,:;.!?]|$)/gi, ' is '],
        [/'re([ ,:;.!?]|$)/gi, ' are '],
        [/'ve([ ,:;.!?]|$)/gi, ' have '],
        [/'m([ ,:;.!?]|$)/gi, ' am '],
        [/'d([ ,:;.!?]|$)/gi, ' had ']
      ],
      contractionsBase = { // for unquoted contractions
        cannot: ['can', 'not'],
        gonna: ['going', 'to'],
        wanna: ['want', 'to']
      };
  
  // collection of english stopwords
  langEn.stopwords = ["about","above","after","again","all","also","am","an","and",
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
  ];
  
  // normalizes a string
  langEn.normalize = function(s) {
    return s.normalize(form).replace(codePoints, "")
  }
  
  // tokenizes a string
  langEn.tokenize = function(s) {
    s = s.toLowerCase();
    var i, p, l, r = [], f = [];
    for (i = 0; i < replacements.length; i++) s = s.replace(replacements[i][0], replacements[i][1]); // expand single quoted word
    p = s.split(punctuations); // extract by punctuations
    for (i = 0; i < p.length; i++) { // expand contracted words
      l = p[i];
      if (hasProp(contractionsBase, l)) Array.prototype.push.apply(r, contractionsBase[l]);
      else r.push(p[i]);
    };
    for (i = 0; i < r.length; i++) if (r[i].length) f.push(r[i]); // filter words
    return f;
  }
  
  // extract terms in the provided string
  langEn.split = function(s) {
    return langEn.tokenize(langEn.normalize(s));
  }
  
  // returns true if s is a stopword
  langEn.stop = function(s) {
    return langEn.stopwords.includes(s);
  }
  
 // Porter Stemmer
 // Modified to fasten itself
 
  var step2list = {
      "ational" : "ate",
      "tional" : "tion",
      "enci" : "ence",
      "anci" : "ance",
      "izer" : "ize",
      "bli" : "ble",
      "alli" : "al",
      "entli" : "ent",
      "eli" : "e",
      "ousli" : "ous",
      "ization" : "ize",
      "ation" : "ate",
      "ator" : "ate",
      "alism" : "al",
      "iveness" : "ive",
      "fulness" : "ful",
      "ousness" : "ous",
      "aliti" : "al",
      "iviti" : "ive",
      "biliti" : "ble",
      "logi" : "log"
    },

    step3list = {
      "icate" : "ic",
      "ative" : "",
      "alize" : "al",
      "iciti" : "ic",
      "ical" : "ic",
      "ful" : "",
      "ness" : ""
    },

    c = "[^aeiou]",          // consonant
    v = "[aeiouy]",          // vowel
    C = c + "[^aeiouy]*",    // consonant sequence
    V = v + "[aeiou]*",      // vowel sequence

    mgr0 = new RegExp("^(" + C + ")?" + V + C),                     // [C]VC... is m>0
    meq1 = new RegExp("^(" + C + ")?" + V + C + "(" + V + ")?$"),   // [C]VC[V] is m=1
    mgr1 = new RegExp("^(" + C + ")?" + V + C + V + C),             // [C]VCVC... is m>1
    s_v = new RegExp("^(" + C + ")?" + v),                          // vowel in stem
    
    // instantiate these regex once
    ra = /^(.+?)(ss|i)es$/,
    rb = /^(.+?)([^s])s$/,
    rc = /^(.+?)eed$/,
    rd = /^(.+?)(ed|ing)$/,
    re = /.$/,
    rf = /(at|bl|iz)$/,
    rg = new RegExp("([^aeiouylsz])\\1$"),
    rh = new RegExp("^" + C + v + "[^aeiouwxy]$"),
    ri = /^(.+?)y$/,
    rj = /^(.+?)(ational|tional|enci|anci|izer|bli|alli|entli|eli|ousli|ization|ation|ator|alism|iveness|fulness|ousness|aliti|iviti|biliti|logi)$/,
    rk = /^(.+?)(icate|ative|alize|iciti|ical|ful|ness)$/,
    rl = /^(.+?)(al|ance|ence|er|ic|able|ible|ant|ement|ment|ent|ou|ism|ate|iti|ous|ive|ize)$/,
    rm = /^(.+?)(s|t)(ion)$/,
    rn = /^(.+?)e$/,
    ro = /ll$/;

  langEn.stem = function (w) {
    var   stem,
      suffix,
      firstch,
      origword = w;
    
    if (w.length < 3) { return w; }
    
    firstch = w.substr(0,1);
    if (firstch == "y") {
      w = firstch.toUpperCase() + w.substr(1);
    }
    
    // Step 1a
    if (ra.test(w)) { w = w.replace(ra,"$1$2"); }
    else if (rb.test(w)) {  w = w.replace(rb,"$1$2"); }
    
    // Step 1b
    if (rc.test(w)) {
      var fp = rc.exec(w);
      if (mgr0.test(fp[1])) {
        w = w.replace(re,"");
      }
    } else if (rd.test(w)) {
      var fp = rd.exec(w);
      stem = fp[1];
      if (s_v.test(stem)) {
        w = stem;
        if (rf.test(w)) {  w = w + "e"; }
        else if (rg.test(w)) { w = w.replace(re,""); }
        else if (rh.test(w)) { w = w + "e"; }
      }
    }
    
    // Step 1c
    if (ri.test(w)) {
      var fp = ri.exec(w);
      stem = fp[1];
      if (s_v.test(stem)) { w = stem + "i"; }
    }
    
    // Step 2;
    if (rj.test(w)) {
      var fp = rj.exec(w);
      stem = fp[1];
      suffix = fp[2];
      if (mgr0.test(stem)) {
        w = stem + step2list[suffix];
      }
    }
    
    // Step 3
    if (rk.test(w)) {
      var fp = rk.exec(w);
      stem = fp[1];
      suffix = fp[2];
      if (mgr0.test(stem)) {
        w = stem + step3list[suffix];
      }
    }
    
    // Step 4
    if (rl.test(w)) {
      var fp = rl.exec(w);
      stem = fp[1];
      if (mgr1.test(stem)) {
        w = stem;
      }
    } else if (rm.test(w)) {
      var fp = rm.exec(w);
      stem = fp[1] + fp[2];
      if (mgr1.test(stem)) {
        w = stem;
      }
    }
    
    // Step 5
    if (rn.test(w)) {
      var fp = rn.exec(w);
      stem = fp[1];
      if (mgr1.test(stem) || (meq1.test(stem) && !(rh.test(stem)))) {
        w = stem;
      }
    }
    
    if (ro.test(w) && mgr1.test(w)) {
      w = w.replace(re,"");
    }
    
    // and turn initial Y back to y
    
    if (firstch == "y") {
      w = firstch.toLowerCase() + w.substr(1);
    }
    
    return w;
  };
  
  return langEn;
})();

// custom events emitter
function EventEmitter() {
  this.eventListeners = {};
  this.id = 0;
};

EventEmitter.prototype = {
  addEventListener: function(ev, fn, opt) {
    if (typeof ev != "string") throw "EventEmitter.prototype.addEventListener() argument 0 'ev' must be a string!";
    if (typeof fn != "function") throw "EventEmitter.prototype.addEventListener() argument 1 'fn' must be a function!";
    if (!opt) opt = {};
    var id = this.id += 1,
        obj = {};
    obj.fn = fn;
    obj.ev = ev.toLowerCase();
    obj.once = !!opt.once;
    this.eventListeners[id] = obj;
    return id;
  },
  removeEventListener: function(idx) {
    this.eventListeners[idx] = null;
  },
  dispatchEvent: function(ev, args, action) {
    if (typeof ev != "string") throw "EventEmitter.prototype.dispatch() argument 0 'ev' must be a string!";
    if (!ev.length) throw "Event name cannot be empty!";
    if (!args) args = [];
    ev = ev.toLowerCase();
    var i, l, s = {}, stl = "on" + ev,
        f = typeof action == "function";
    s.type = ev;
    if (f) s.cancel = false;
    if (typeof this[stl] == "function") this[stl].call(s, args);
    for (i in this.eventListeners) {
      l = this.eventListeners[i];
      if (!l) continue;
      if (l.ev == ev || !l.ev.length)
        this.eventListeners[i].fn.call(s, args);
      if (l.once) this.eventListeners[i] = null;
    };
    if (!s.cancel && f) action.call(s);
  }
};

Object.setPrototypeOf(doc, new EventEmitter());

function removeQueryHighlight() {
  doc.unhighlight(contentEl[0]);
  var url = new URL(document.location);
  url.searchParams.delete("highlight");
  window.history.replaceState({}, "", url)
};

_window.ready(function(readyEvent) {
  // website root location
  doc.root = doc.page.location.replace(/[^\/]+/g, "..").slice(3);
  if (!doc.root.length) doc.root = ".";
  doc.root += "/";
  
  var contentEl = $(".content");
  
  var searchBar = $("input[type=search]").first();
  
  // highlight page contents
  if (doc.query.highlight) {
    for (var i = 0; i < doc.query.highlight.length; i++)
      doc.highlight(doc.query.highlight[i], contentEl[0]);
  }
  
  // toc highlight
  var headings = contentEl.find("h1,h2,h3,h4,h5,h6"),
      tocEl = $(".toc"),
      docBody = $(".main"),
      backtotop = $(".backtotop"),
      mainEl = $(".main");
  
  backtotop.click(function(e) {
    e.preventDefault();
    mainEl.scrollTop(0);
  });
  
  mainEl.scroll(function() {
    var scrollTop = mainEl.scrollTop();
    
    // back to top button
    if (scrollTop > 20) backtotop.css("right", "4px");
    else backtotop.css("right", "-60px");
    
    tocEl.find("a.current").removeClass("current");
    var idx, heading;
    for (idx = headings.length - 1; idx > -1; idx--) {
      heading = $(headings[idx]);
      if (scrollTop > heading.offset().top - 75) {
        tocEl.find("a[href=\"#" + heading.attr("id") + "\"]").addClass("current");
        break;
      }
    };
  });
  
  // copy buttons
  $(".snippet td.code pre, .snippet > pre").each(function() {
    var elm = $(this);
    var text = elm.text().trim();
    elm.contents().first().click(function (e) {
      e.preventDefault();
      navigator.clipboard.writeText(text).then(function() {
        console.log("Copied snippet to clipboard!")
      }).catch(function(err) {
        console.error("Failed to copy on clipboard: " + err)
      })
    })
  });
  
  // key events
  var keySkipTags = ["BUTTON","INPUT","SELECT","TEXTAREA"];
  _document.keydown(function(e) {
    if (keySkipTags.includes(document.activeElement.tagName)) return;
    if (!e.metaKey && !e.altKey) {
      if (e.ctrlKey) {
        if (e.key == "/") searchBar.focus();
      }
      else if (!e.shiftKey) {
        if (e.key == "ArrowLeft") document.location.href = doc.root + doc.page.previous;
        else if (e.key == "ArrowRight") document.location.href = doc.root + doc.page.next;
        else if (e.key == "Escape") removeQueryHighlight();
      }
    }
  });
  
  // toast element
  var toastBox = $(".toast");
  
  function toastHandler() {
    toastBox.removeClass("active");
    var item = queuedToasts.shift();
    if (!item) return;
    var lastToast = toastBox[0].childNodes[0];
    if (lastToast) toastBox[0].removeChild(lastToast);
    toastBox.append($("<div>" + item + "</div>"));
    toastBox.addClass("active");
    console.log("toast shown");
    setTimeout(function() {
      toastBox.removeClass("active");
      if (queuedToasts.length) toastHandler();
    }, 5000)
    doc.dispatchEvent("toastShown", item);
  }
  
  // automatically show the toast on queue
  doc.addEventListener("toastQueued", function() {
    if (queuedToasts.length === 1) toastHandler();
  })
  
  // show toasts queued before the dom fully loaded
  if (queuedToasts.length) toastHandler();
  
  // trigger ready event
  doc.dispatchEvent("ready", [readyEvent]);
});

// for var
return doc;

});
