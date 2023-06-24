doc.addEventListener("searchReady", function readyFunction() {
  // make sure that dom is fully loaded
  if (!$.isReady) return doc.onready = readyFunction;
  
  var resultList = $("#results"),
      searchBar = $("input[type=search]").first(),
      searchState = $("#state");
  searchState.text("Index loaded");
  if (doc.query.q && doc.query.q[0].length) {
    document.title = "Search: " + doc.query.q[0];
    searchBar.val(doc.query.q[0]);
    perform();
  };
  var slash = /\//g;
  var subSlash = " &#187; ";
  
  // performs the search
  function perform(q) {
    searchState.text("Searching...");
    if (!q) q = doc.query.q[0];
    var start = Date.now();
    var eq = encodeURIComponent(q);
    var i, x, n, d, p;
    var results = doc.search(q);
    var deltaTime = (Date.now() - start) / 1000;
    searchState.text("Found " + results.length + " results in " + deltaTime + " seconds.");
    setTimeout(addItem, 15, 0);
    function addItem(i) {
      x = results[i];
      d = doc.index.docfiles[x.ref];
      p = d.location.substr(3).replace(slash, subSlash);
      n = $("<div><a style=\"display: block; color: #444 !important; text-decoration: none;\" href=\"" + x.path + ".html?highlight=" + eq + "\"><h2 class=\"no-offset\">" + x.title + "</h2><small>" + p + "</small></a><p>" + d.about + "</p></div>")
      resultList.append(n);
      i++;
      if (i < results.length) setTimeout(addItem, 15, i);
    }
  };
});

