package producer;

import com.fasterxml.jackson.annotation.JsonIgnore;

public class TransactionEvent {
    private String userId;
    private double amount;
    private String timestamp;
    private double latitude;
    private double longitude;
    private String ipAddress;

    public TransactionEvent() {}

    public TransactionEvent(String userId, double amount, String timestamp,
                            double latitude, double longitude, String ipAddress) {
        this.userId = userId;
        this.amount = amount;
        this.timestamp = timestamp;
        this.latitude = latitude;
        this.longitude = longitude;
        this.ipAddress = ipAddress;
    }

    public String getUserId() { return userId; }
    public double getAmount() { return amount; }
    public String getTimestamp() { return timestamp; }
    public double getLatitude() { return latitude; }
    public double getLongitude() { return longitude; }
    public String getIpAddress() { return ipAddress; }

    @JsonIgnore
    public boolean isHighAmount() {
        return amount > 5000;
    }

    @JsonIgnore
    public boolean isSuspiciousLocation() {
        return latitude < 20.0 || longitude < -120.0;
    }

    @JsonIgnore
    public boolean isSuspiciousIp() {
        return ipAddress.equals("192.168.1.1") || ipAddress.equals("10.0.0.1");
    }

    @Override
    public String toString() {
        return String.format("TransactionEvent(userId=%s, amount=%.2f, timestamp=%s, lat=%.2f, lon=%.2f, ip=%s)",
                userId, amount, timestamp, latitude, longitude, ipAddress);
    }
}
