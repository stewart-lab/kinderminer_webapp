import json
import datetime
import requests
import time
import secret

from requests.auth import HTTPBasicAuth

# some constants for search
URL_BASE = secret.query_url_base
AUTH = HTTPBasicAuth(secret.query_user, secret.query_pass)


class MatchText:
    def __init__(self, text, tokenize, stem, alias, delimiter):
        text = text.strip()
        self.use_tokens = tokenize
        self.use_stemming = stem
        self.use_aliases = alias
        self.text = text.split(delimiter) if alias else [text]
        self.delimiter = delimiter
        self._tok_texts = [t.split() for t in self.text] if tokenize else None

    def _make_match_phrase_list(self, phrases):
        analyzer = 'abstract.english' if self.use_stemming else 'abstract'
        ret = [{'match_phrase': {analyzer: p}} for p in phrases]
        return ret

    def make_match_bool(self):
        ret = None
        # if not using aliases, there's just one item (tokens or not)
        if not self.use_aliases:
            # grab either the single phrase as a list or the list of tokens
            phrases = self.text if not self.use_tokens else self._tok_texts[0]
            # this can just be a must list
            must = self._make_match_phrase_list(phrases)
            ret = {'bool': {'must': must}}
        # otherwise there is more than one string in the phrases
        else:
            # this will be a should match
            should = None
            # if no tokenization, it's a flat should across the aliases
            if not self.use_tokens:
                should = self._make_match_phrase_list(self.text)
            # otherwise it is a should across musts for the tokens
            else:
                should = []
                # make a must for each token list
                for tok_list in self._tok_texts:
                    must = self._make_match_phrase_list(tok_list)
                    should.append({'bool': {'must': must}})
            # wrap it up
            ret = {'bool': {'should': should}}
        # done
        return ret

    def get_name(self):
        # just give back the one name if not using aliases
        if not self.use_aliases:
            return self.text[0]
        # otherwise make a comma-separated-list
        return self.delimiter.join(self.text)

# this is the API version used for the web interface


def api_full_query(
        all_targets,
        key_phrase,
        through_year,
        sep_kp,
        stem_kp=False,
        sep_targ=False,
        stem_targ=False,
        alias=False,
        delim=','):
    # first make our keyphrase
    keyphrase_mt = MatchText(key_phrase, sep_kp, stem_kp, alias, delim)
    # and prepare all the target terms
    targ_list = [MatchText(t, sep_targ, stem_targ, alias, delim)
                 for t in all_targets]
    # we will return this as a dictionary stored somewhat compactly
    ret = dict()
    # compute the total number of articles in the database
    db_article_cnt = get_db_count(through_year, URL_BASE, AUTH)
    ret['db_article_cnt'] = db_article_cnt
    # and the number of times the key phrase shows up
    kp_cnt = get_kp_count(keyphrase_mt, through_year, URL_BASE, AUTH)
    ret['kp_cnt'] = kp_cnt
    # and do each target
    ret['target'] = list()
    ret['targ_cnt'] = list()
    ret['targ_with_kp_cnt'] = list()
    for targ_mt in targ_list:
        targ_cnt, targ_with_kp_cnt = get_targ_and_targkp_count(
            targ_mt, keyphrase_mt, through_year, URL_BASE, AUTH, kp_cnt=kp_cnt)
        ret['target'].append(targ_mt.get_name())
        ret['targ_cnt'].append(targ_cnt)
        ret['targ_with_kp_cnt'].append(targ_with_kp_cnt)
    return ret


def make_query_object(target_mt, keyphrase_mt, through_year):
    # build the constraint list first
    must = []
    # are we searching on a target term
    if target_mt is not None:
        must.append(target_mt.make_match_bool())
    # and key phrase
    if keyphrase_mt is not None:
        must.append(keyphrase_mt.make_match_bool())
    # always add the year constraint
    must.append({'range': {'publication_date.year': {'lte': through_year}}})
    query = {'query': {'bool': {'must': must}}}
    return query


def try_get(url, data, auth):
    timeout = 5.0
    backoff = 1.0
    max_backoff = 30.0
    res = None
    done = False
    while not done:
        # try to do the query
        try:
            res = requests.get(url, data=data, auth=auth, timeout=timeout)
        except (requests.ConnectionError, requests.HTTPError, requests.Timeout):
            # should do something more here, perhaps specific to each error
            pass
        # did we get a good response
        if res is not None and res.status_code == 200:
            done = True
        else:
            res = None
            # we didn't get what we wanted, so retry with a backoff
            backoff = min(backoff * 2.0, max_backoff)
            time.sleep(backoff)
    return res


def get_count(target_mt, keyphrase_mt, through_year, url_base, auth):
    # target term and/or key phrase may be None
    q = make_query_object(target_mt, keyphrase_mt, through_year)
    res = try_get(url_base, json.dumps(q), auth)
    ret_cnt = res.json()['count']
    return ret_cnt


def get_db_count(through_year, url_base, auth):
    return get_count(None, None, through_year, url_base, auth)


def get_kp_count(keyphrase_mt, through_year, url_base, auth):
    return get_count(None, keyphrase_mt, through_year, url_base, auth)


def get_targ_and_targkp_count(
        target_mt,
        keyphrase_mt,
        through_year,
        url_base,
        auth,
        kp_cnt=None):
    # we may get a kp_cnt to speed up querying or we should compute
    if kp_cnt is None:
        kp_cnt = get_kp_count(keyphrase_mt, through_year, url_base, auth)
    # default to 0 for the combined match
    targ_with_kp_cnt = 0
    # first the individual count
    targ_cnt = get_count(target_mt, None, through_year, url_base, auth)
    # only need to query combined if articles exist for both individually
    if targ_cnt > 0 and kp_cnt > 0:
        # now do both key phrase and target
        targ_with_kp_cnt = get_count(
            target_mt, keyphrase_mt, through_year, url_base, auth)
    return targ_cnt, targ_with_kp_cnt
