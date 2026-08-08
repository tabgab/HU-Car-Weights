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

    @Test fun thresholdIsUniform() {
        // Single 2000 kg rule for every powertrain (and unknown ones).
        assertEquals(2000, FeeClassifier.thresholdFor("BEV"))
        assertEquals(2000, FeeClassifier.thresholdFor("PHEV"))
        assertEquals(2000, FeeClassifier.thresholdFor("ICE"))
        assertEquals(2000, FeeClassifier.thresholdFor(null))
    }

    @Test fun representativeValueCases() {
        assertEquals(FeeStatus.DOUBLE, FeeClassifier.classify("BEV", 2100))
        assertEquals(FeeStatus.OK,     FeeClassifier.classify("BEV", 1950))
        assertEquals(FeeStatus.DOUBLE, FeeClassifier.classify("PHEV", 2050))
        assertEquals(FeeStatus.OK,     FeeClassifier.classify("PHEV", 1900))  // was double under the old 1800 rule
        assertEquals(FeeStatus.OK,     FeeClassifier.classify("ICE",  1850))  // was double under the old 1800 rule
        assertEquals(FeeStatus.DOUBLE, FeeClassifier.classify("ICE",  2001))
    }

    @Test fun boundaryIsOk() {
        // exactly at threshold = ok (strict >)
        assertEquals(FeeStatus.OK, FeeClassifier.classify("BEV",  2000))
        assertEquals(FeeStatus.OK, FeeClassifier.classify("ICE",  2000))
        assertEquals(FeeStatus.OK, FeeClassifier.classify("PHEV", 2000))
    }

    @Test fun rangeCases() {
        assertEquals(FeeStatus.BORDERLINE, FeeClassifier.classify("ICE", null, 1950, 2050))  // straddles 2000
        assertEquals(FeeStatus.BORDERLINE, FeeClassifier.classify("BEV", null, 1950, 2050))
        assertEquals(FeeStatus.DOUBLE,     FeeClassifier.classify("ICE", null, 2050, 2100))  // entirely above
        assertEquals(FeeStatus.OK,         FeeClassifier.classify("ICE", null, 1600, 1750))  // entirely below
        assertEquals(FeeStatus.OK,         FeeClassifier.classify("ICE", null, 1750, 1850))  // below 2000 now
    }

    @Test fun unknown() {
        assertEquals(FeeStatus.UNKNOWN, FeeClassifier.classify("ICE", null, null, null))
        assertEquals(FeeStatus.UNKNOWN, FeeClassifier.classify("BEV", null))
    }
}
