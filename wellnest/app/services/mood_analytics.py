import numpy as np


class MoodAnalytics:

    @staticmethod
    def compute_trend(moods):
        """
        Linear trend using least squares slope.
        """

        if len(moods) < 2:
            return 0

        x = np.arange(len(moods))
        y = np.array(moods)

        slope = np.polyfit(x, y, 1)[0]

        return float(slope)

    @staticmethod
    def compute_volatility(moods):
        """
        Successive squared difference.
        """

        if len(moods) < 2:
            return 0

        moods = np.array(moods)

        diff = np.diff(moods)

        ssd = np.mean(diff ** 2)

        return float(ssd)

    @staticmethod
    def compute_average(moods):

        if not moods:
            return 0

        return float(np.mean(moods))