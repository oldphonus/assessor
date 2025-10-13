import random
import statistics

class RiskAssessor:
    """
    Анализ финансовых рисков на основе исторических доходностей.
    Поддержка Value-at-Risk (VaR), стресс-тесты, сценарный анализ.
    """
    def __init__(self, returns):
        self.returns = returns

    def value_at_risk(self, confidence=0.95):
        sorted_returns = sorted(self.returns)
        var_index = int((1-confidence) * len(sorted_returns))
        var = abs(sorted_returns[var_index])
        print(f"VaR ({confidence*100:.0f}%) = {var:.2f}")
        return var

    def stress_test(self, stress_scenario):
        stressed = [x + stress_scenario for x in self.returns]
        avg = statistics.mean(stressed)
        print(f"Среднее значение при шоковом сценарии: {avg:.2f}")
        return avg

    def plot_distribution(self):
        try:
            import matplotlib.pyplot as plt
            plt.hist(self.returns, bins=20, color="blue", alpha=0.7)
            plt.title("Распределение доходностей")
            plt.xlabel("Доходность, %")
            plt.show()
        except ImportError:
            print("Для графиков установите matplotlib")

    def report(self):
        print(f"Средняя доходность: {statistics.mean(self.returns):.2f}, Стд: {statistics.stdev(self.returns):.2f}")

if __name__ == "__main__":
    ret = [random.gauss(1.5, 8) for _ in range(100)]
    ra = RiskAssessor(ret)
    ra.value_at_risk()
    ra.stress_test(-10)
    ra.report()
    ra.plot_distribution()
