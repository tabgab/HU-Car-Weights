package com.tabigabor.carweights.data

import com.tabigabor.carweights.domain.CarDecision
import com.tabigabor.carweights.domain.FeeClassifier
import com.tabigabor.carweights.domain.Policy
import com.tabigabor.carweights.domain.PolicyOutcome

object PolicySimulator {
    fun run(cars: List<com.tabigabor.carweights.domain.Car>, policy: Policy): PolicyOutcome {
        val decisions = cars.map { c ->
            val t = policy.thresholdFor(c.powertrainType)
            val status = FeeClassifier.classify(c.powertrainType, c.weight, c.weightMin, c.weightMax)
            CarDecision(car = c, threshold = t, feeStatus = status)
        }
        return PolicyOutcome(policy = policy, decisions = decisions)
    }
}
