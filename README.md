# KinderMiner Web: A Simple Web Tool for Ranking Pairwise Associations in Biomedical Applications

The web application is freely available for use at [https://www.kinderminer.org](https://www.kinderminer.org).


This repository hosts the code for the web application.


### Brief Description

Many important scientific discoveries require lengthy experimental processes of trial and error and could benefit from intelligent prioritization based on deep domain understanding.
While exponential growth in the scientific literature makes it difficult to keep current in even a single domain, that same rapid growth in literature also presents an opportunity for automated extraction of knowledge via text mining.
We have developed a web application implementation of the KinderMiner algorithm for proposing ranked associations between a list of target terms and a key phrase.
Any key phrase and target term list can be used for biomedical inquiry.
We built the web application around a text index derived from PubMed.
It is the first publicly available implementation of the algorithm, is fast and easy to use, and includes an interactive analysis tool.
The KinderMiner web application is a public resource offering scientists a cohesive summary of what is currently known about a particular topic within the literature, and helping them to prioritize experiments around that topic.
It performs comparably or better to similar state-of-the-art text mining tools, is more flexible, and can be applied to any biomedical topic of interest.
It is also continually improving with quarterly updates to the underlying text index and through response to suggestions from the community.


### Dependencies

* Python 3.7.2
* Flask 1.0.2
* Flask-MySQL 1.4.0
* PyMySQL 0.9.3
* MariaDB 5.5.65
* SciPy 1.2.0
* Postmarker 0.13.0

The code for building the backend PubMed text index is available at [https://github.com/iross/km_indexer](https://github.com/iross/km_indexer).
