---
title: Search engine
about: A documentation about the docs search algorithm
contributors: VYT <https://github.com/vytdev>
keywords: search, docs
---

VYT Documentation uses a full-text search engine.

## How it works?

This search works with an index of all document files in this site that was built.
It is based not in crawling, but in the built pages. The generator builds the index
by extracting important informations on each page (text/words and metadata) after
generating the content. Each word that the generator found in the documents are
counted for the page and for the whole corpus of documents. It is used for calculating
the relevance of the document as you (the user) request a query from search. It
uses the [Okapi BM25 algorithm](https://en.m.wikipedia.org/wiki/Okapi_BM25), it is
a function in retrieving the relevance of a document (page) on the given query (search)
over the corpus. However, it isn't fully implemented because I still didn't know
how Binary Independence Model was calculated. Here is how it is being calculated:

### Term Frequency

It is calculated by getting the ratio of the count of the given term in the given
document to the total count of terms found in the given document.

    ti / |D|


Where,

- `ti` is the number of repitition of term *i* in the document *D*
- `|D|` is the count of all terms in the document *D*

### Inverse Document Frequency

It is calculated by getting the ratio of the count of the given term in the whole
corpus to the total count of terms found in corpus.

    dfi / |C|

Where,

- `dfi` is the number of repitition of term *i* in the whole corpus
- `|C|` is the count of all terms in the whole corpus

But here, we use this variant:

    ((ri + 1/2)/(R - ri + 1/2))/((dfi - ri + 1/2)/(N - R - dfi + ri +1/2))

Where,

- `ri` is the number of relevant documents containing the term *i*
- `R` is the total count of relevant documents
- `N` is the total count of the documents in the corpus

Somehow, it is normalized by getting its natural logarithm, it is called **Smoothing**.
This step helps the output to give more accurate results.

However, the formula of the IDF is slightly modified. It is because the sometimes
the variant we used returns a negative number causing the log to return `NaN`. It
is fixed by adding additional 1 to the result before getting the log.

## Expressions

!!! warning
    
    This support doesn't implemented yet, but were working on it.

Expressions help you to search for terms
