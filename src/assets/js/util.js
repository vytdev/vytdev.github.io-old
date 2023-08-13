/* ================================================================
Support compatibility between browsers
================================================================ */
(function() {
    // support Array.prototype.sort
    if (typeof Array.prototype.sort != "function") {
        // default sorting condition, sorts like dictionaries
        function lexicographSort(a, b) {
            a = "" + a;
            b = "" + b;
            return a > b
                ? 1
                : a < b
                    ? -1
                    : 0;
        };
        // this behaves exactly like the native function:
        //    arr.sort(() => -1); // reverses an array as expected
        //    arr.sort(() => 0);  // does noting in the array order, same with 1 or NaN
        // Quick Sort algorithm (see https://en.m.wikipedia.org/wiki/Quicksort)
        Array.prototype.sort = function(con) {
            // This sort method speed depends on the:
            //  - Order of items (if the array is already sorted or not)
            //  - Difference between items (higher difference - slower it takes to finish)
            //  - The conditioning function (on how conditioning function works)

            // prevent multiple calls
            if (this.length <= 1) return this;
            // no condition fn provided, use default lexicographic sorting
            if (typeof con != "function")
                con = lexicographSort;
            // declare vars
            var len = this.length - 1,
                pivot = this[len],
                left = [],
                right = [],
                idx, compared, val;
            // here's the conditioning runs
            for (idx = 0; idx < len; idx++) {
                compared = this[idx];
                val = con(pivot, compared);
                if (isNaN(val) || val >= 0) {
                    left.push(compared);
                } else {
                    right.push(compared)
                }
            }
            // return result
            var result = left.sort(con);
            result.push(pivot);
            result = result.concat(right.sort(con));
            len = result.length;
            // update array
            for (idx = 0; idx < len; idx++) {
                this[idx] = result[idx];
            }
            return this;
        }
    }
})();

/* ================================================================
Handle website behaviour
================================================================ */
(function() {
    var doc = window.doc = {};
    "use strict";

    // copies contents of src to dest
    doc.merge = function (src, dest, skipExists) {
        var prop;
        for (prop in src) {
            if (hasProp(src, prop)) {
                if (skipExists && hasProp(dest, prop)) continue;
                dest[prop] = src[prop];
            }
        }
        return dest;
    }

    // short names of common functions for faster retrival
    var hasProp = Function.prototype.call.bind(Object.prototype.hasOwnProperty),
        setProto = Object.setPrototypeOf
            || ({ __proto__: [] } instanceof Array && function(a, b) { a.__proto__ = b; })
            ||  doc.merge;

    var rwhitespace = /\s+/g,
        rurlquerydecode = /\+/g;

    // add queries
    doc.query = (function() {
        var query = document.location.search;
        var parts = query.slice(query.indexOf("?") + 1).split("&");
        var output = {};
        var i, sepidx, part, key, val;
        for (i = 0; i < parts.length; i++) {
            part = parts[i];
            sepidx = part.indexOf("=");
            key = decodeURIComponent((sepidx == -1 ? part: part.substr(0, sepidx)).replace(rurlquerydecode, " "));
            val = decodeURIComponent((sepidx == -1 ? part: part.substr(sepidx + 1, part.length)).replace(rurlquerydecode, " "));
            output[key] = val;
        };
        return output;
    })();

    // highlights text on the doc (keeps the markup intact)
    var highlightSkipTags = ["BUTTON", "SELECT", "TEXTAREA", "SVG"],
        highlightClass = "highlight",
        noHighlightClass = "nohighlight";
    doc.highlight = function(text, node) {
        if (!node) node = document.body || document.documentElement;
        if (typeof text != "string") throw "doc.highlight first argument 'text' must be a string!"
        var a = text.toLowerCase().split(rwhitespace); // highlight multiple words
        if (node.nodeType == document.TEXT_NODE) {
            if (node.parentNode.classList.contains(noHighlightClass) || node.parentNode.classList.contains(highlightClass)) return;
            var i, t, p, s, l, v,
                c = node.nodeValue;
                v = c.toLowerCase(); // lower case for finding indices
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
        } else if (!highlightSkipTags.includes(node.tagName)) {
            var i,
            n;
            for (i = 0; i < node.childNodes.length; i++) {
                n = node.childNodes[i];
                doc.highlight(text, n);
            }
        }
    }

    // remove the current highlights on document
    doc.unhighlight = function(node) {
        if (!node) node = document.body || document.documentElement;
        if (node.tagName == "SPAN" && node.className == highlightClass) {
            var p = node.previousSibling,
            n = node.nextSibling,
            r = node.parentNode,
            t = "",
            b = node;
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
        } else if (node.nodeType != document.TEXT_NODE) {
            var i, n, m,
                l = node.childNodes.length;
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
            var i, l,
                s = {},
                stl = "on" + ev,
                f = typeof action == "function";
            s.type = ev;
            if (f) s.cancel = false;
            if (typeof this[stl] == "function") this[stl].call(s, args);
            for (i in this.eventListeners) {
                l = this.eventListeners[i];
                if (!l) continue;
                if (l.ev == ev || !l.ev.length)
                    this.eventListeners[i].fn.apply(s, args);
                if (l.once) this.eventListeners[i] = null;
            };
            if (!s.cancel && f) action.call(s);
        }
    };

    setProto(doc, new EventEmitter());

    function removeQueryHighlight() {
        doc.unhighlight(contentEl[0]);
        var url = new URL(document.location);
        url.searchParams.delete("highlight");
        window.history.replaceState( {}, "", url)
    };

    // wait for page data until loaded
    doc.addEventListener("dataLoaded", function(page) {
        // website root location
        doc.root = page.location.replace(/[^\/]+/g, "..").slice(3);
        if (!doc.root.length) doc.root = ".";
        doc.root += "/";
    },
        {
            once: true
        });

    // this part needs jQuery
    if (!hasProp(window, "jQuery")) throw "jQuery not found!";

    var _document = $(document),
        _window = $(window);

    // wait until dom fully loaded
    _window.ready(function(readyEvent) {
        var contentEl = $(".article");

        var searchBar = $("input[type=search]").first();

        // highlight page contents
        if (doc.query.highlight) {
            doc.highlight(doc.query.highlight, contentEl[0])
        }

        // sidebar behaviour for devices <768px width
        var sidebarToggle = $("#sidebar-toggle"),
        sidebarElem = $(".sidebar");

        sidebarToggle.click(function() {
            if (sidebarToggle.prop("checked")) sidebarElem.css("left", "0");
            else sidebarElem.css("left", "-330px");
        })

        $(".footer, .article").click(function(ev) {
            if (sidebarToggle.prop("checked")) sidebarToggle.click();
        })

        // toc highlight and back-to-top btn
        var headings = contentEl.find("h1,h2,h3,h4,h5,h6"),
        tocEl = $(".toc"),
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

            // toc highlight
            tocEl.find("a.current").removeClass("current");
            var idx,
            heading;
            for (idx = headings.length - 1; idx > -1; idx--) {
                heading = $(headings[idx]);
                if (scrollTop >= scrollTop + heading.offset().top - 80) {
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
        var keySkipTags = ["BUTTON", "INPUT", "SELECT", "TEXTAREA"];
        _document.keydown(function(e) {
            if (keySkipTags.includes(document.activeElement.tagName)) return;
            if (!e.metaKey && !e.altKey) {
                if (e.ctrlKey) {
                    if (e.key == "/") searchBar.focus();
                } else if (!e.shiftKey) {
                    if (e.key == "ArrowLeft") document.location.href = doc.root + doc.page.previous;
                    else if (e.key == "ArrowRight") document.location.href = doc.root + doc.page.next;
                    else if (e.key == "Escape") removeQueryHighlight();
                }
            }
        });

        // trigger ready event
        doc.dispatchEvent("ready", [readyEvent]);
    });
})();