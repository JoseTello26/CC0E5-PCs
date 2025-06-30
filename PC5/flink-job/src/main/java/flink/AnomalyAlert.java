package flink;

import java.util.List;

public class AnomalyAlert {
    private String userId;
    private int eventCount;
    private List<String> anomalies;
    private String detectionTime;
    private long windowStart;
    private long windowEnd;

    public AnomalyAlert() {}

    public AnomalyAlert(String userId, int eventCount, List<String> anomalies,
                        String detectionTime, long windowStart, long windowEnd) {
        this.userId = userId;
        this.eventCount = eventCount;
        this.anomalies = anomalies;
        this.detectionTime = detectionTime;
        this.windowStart = windowStart;
        this.windowEnd = windowEnd;
    }

    public String getUserId() {
        return userId;
    }

    public int getEventCount() {
        return eventCount;
    }

    public List<String> getAnomalies() {
        return anomalies;
    }

    public String getDetectionTime() {
        return detectionTime;
    }

    public long getWindowStart() {
        return windowStart;
    }

    public long getWindowEnd() {
        return windowEnd;
    }

    @Override
    public String toString() {
        return String.format("AnomalyAlert{userId='%s', eventCount=%d, anomalies=%s, " +
                        "detectionTime='%s', window=[%d, %d]}",
                userId, eventCount, anomalies, detectionTime, windowStart, windowEnd);
    }
}
