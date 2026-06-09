package com.tabigabor.carweights

import com.tabigabor.carweights.domain.FeeClassifier
import com.tabigabor.carweights.domain.FeeStatus
import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Mirrors tests/test_fees.py 1:1 — the contract for the fee classifier.
 * If these pass, the Android classifier and the web classifier are in lockstep.
 */
class FeeClassifierTest {

    @Test fun thresholdSelection() {
        assertEquals(2000, FeeClassifier.thresholdFor("BEV"))
        assertEquals(1800, FeeClassifier.thresholdFor("PHEV"))
        assertEquals(1800, FeeClassifier.thresholdFor("ICE"))
    }

    @Test fun representativeValueCases() {
        assertEquals(FeeStatus.DOUBLE, FeeClassifier.classify("BEV", 2100))   // BEV over 2000
        assertEquals(FeeStatus.OK,     FeeClassifier.classify("BEV", 1950))
        assertEquals(FeeStatus.DOUBLE, FeeClassifier.classify("PHEV", 1900))  // PHEV uses 1800
        assertEquals(FeeStatus.OK,     FeeClassifier.classify("PHEV", 1700))
        assertEquals(FeeStatus.OK,     FeeClassifier.classify("ICE",  1700))
        assertEquals(FeeStatus.DOUBLE, FeeClassifier.classify("ICE",  1850))
    }

    @Test fun boundaryIsOk() {
        assertEquals(FeeStatus.OK, FeeClassifier.classify("BEV", 2000))  // exactly at threshold = ok (strict >)
        assertEquals(FeeStatus.OK, FeeClassifier.classify("ICE",  1800))
    }

    @Test fun rangeCases() {
        assertEquals(FeeStatus.BORDERLINE, FeeClassifier.classify("ICE", null, 1750, 1850))  // straddles 1800
        assertEquals(FeeStatus.BORDERLINE, FeeClassifier.classify("BEV", null, 1950, 2050))  // straddles 2000
        assertEquals(FeeStatus.DOUBLE,     FeeClassifier.classify("ICE", null, 1850, 1900))  // entirely above
        assertEquals(FeeStatus.OK,         FeeClassifier.classify("ICE", null, 1600, 1750))  // entirely below
    }

    @Test fun unknown() {
        assertEquals(FeeStatus.UNKNOWN, FeeClassifier.classify("ICE", null, null, null))
        assertEquals(FeeStatus.UNKNOWN, FeeClassifier.classify("BEV", null))
    }
}
