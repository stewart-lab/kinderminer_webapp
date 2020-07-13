import scipy.stats as stats
import numpy as np

# this is the function used for the web interface, main code currently makes
# assumption that we have file inputs, which we don't for the webapp


def api_compute_fets(count_object):
    ####################################
    # count_object is a dictionary with:
    # db_article_cnt - total count of articles
    # kp_cnt - count of hits for the keyphrase
    # target - list of the target names in order
    # targ_cnt - list of the target hit counts in target order
    # targ_with_kp_cnt - list of the target & keyphrase hit counts in target order
    ####################################
    # we'll be returning a shallow copy with additional p-value and ratio lists
    ret = count_object.copy()
    ret['fet_p_value'] = list()
    ret['targ_and_kp_ratio'] = list()
    # first grab the fixed totals
    db_tot = int(count_object['db_article_cnt'])
    kp_tot = int(count_object['kp_cnt'])
    # and go through the targets one by one
    targets = count_object['target']
    targ_cnts = count_object['targ_cnt']
    targ_kp_cnts = count_object['targ_with_kp_cnt']
    for i in range(len(targets)):
        targ_tot = int(targ_cnts[i])
        targ_kp = int(targ_kp_cnts[i])
        not_targ_tot = db_tot - targ_tot
        not_kp_tot = db_tot - kp_tot
        # first row is keyphrase, second is NOT keyphrase
        # first col is target, second is NOT target
        targ_kp = targ_kp
        targ_not_kp = targ_tot - targ_kp
        not_targ_kp = kp_tot - targ_kp
        not_targ_not_kp = not_kp_tot - targ_not_kp
        # confusion matrix is specified by row
        confusion_matrix = [[targ_kp, not_targ_kp],
                            [targ_not_kp, not_targ_not_kp]]
        # get the p-value
        odds, p_val = stats.fisher_exact(
            confusion_matrix, alternative='greater')
        # and the ratio (watch divide by zero)
        targ_kp_ratio = 0.0
        if targ_tot > 0:
            targ_kp_ratio = float(targ_kp) / float(targ_tot)
        # and store
        ret['fet_p_value'].append(p_val)
        ret['targ_and_kp_ratio'].append(targ_kp_ratio)
    return ret

