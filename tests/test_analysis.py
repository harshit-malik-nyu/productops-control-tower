import copy
import json
import unittest
from tower.analysis import ROOT, analyze, difference, validate
class AnalysisTests(unittest.TestCase):
    def setUp(self): self.rows=json.loads((ROOT/'fixtures/experiment.json').read_text())['rows']
    def test_hand_calculated_totals(self):
        r=analyze(self.rows)
        self.assertEqual(r['totals']['control']['assigned'],10000)
        self.assertEqual(r['totals']['treatment']['converted'],1350)
        self.assertAlmostEqual(r['primary']['difference'],.015)
        self.assertTrue(.0057<r['primary']['lower_95']<.0059)
    def test_symmetric_interval(self):
        a=difference(100,1000,120,1000);b=difference(120,1000,100,1000)
        self.assertAlmostEqual(a['lower_95'],-b['upper_95'])
    def test_missing_bounds(self):
        r=analyze(self.rows)['missing_outcome_bounds']
        self.assertAlmostEqual(r['lower'],-.005);self.assertAlmostEqual(r['upper'],.035)
    def test_harm_overrides_economics(self):
        r=analyze(self.rows)
        self.assertAlmostEqual(r['economics_scenarios'][1]['monthly_net_assumption'],40000)
        self.assertEqual(r['decision'],'HOLD')
        self.assertTrue(any('Support harm' in s for s in r['reasons']))
    def test_eligible_not_auto_shipped(self):
        for x in self.rows:x['missing']=0;x['support']=50
        self.assertEqual(analyze(self.rows)['decision'],'ELIGIBLE_FOR_REVIEW')
    def test_missing_alone_blocks(self):
        for x in self.rows:x['support']=50
        self.assertEqual(len(analyze(self.rows)['reasons']),1)
    def test_no_benefit_blocks(self):
        for x in self.rows:x['missing']=0;x['support']=50;x['converted']=500
        self.assertTrue(any('Primary' in s for s in analyze(self.rows)['reasons']))
    def test_assignment_imbalance(self):
        self.rows[1]['assigned']=10000
        self.assertLess(analyze(self.rows)['srm_p'],.001)
    def test_sparse_rejected(self):
        with self.assertRaises(ValueError):difference(0,100,1,100)
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):analyze(self.rows+[copy.deepcopy(self.rows[0])])
    def test_invalid_counts(self):
        for val in (-1,1.5,True):
            rows=copy.deepcopy(self.rows);rows[0]['converted']=val
            with self.assertRaises(ValueError):validate(rows)
    def test_impossible_missing(self):
        self.rows[0]['missing']=4900
        with self.assertRaises(ValueError):validate(self.rows)
    def test_order_invariant(self):
        self.assertEqual(analyze(self.rows),analyze(list(reversed(self.rows))))
