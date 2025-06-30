FROM maven:3.8.4-openjdk-17-slim

WORKDIR /app

# Copy pom.xml first for better caching
COPY pom.xml .

# Download dependencies
RUN mvn dependency:go-offline -B

# Copy source code
COPY src/ ./src/

# Build the application
RUN mvn clean package -DskipTests

# Run the application
CMD ["java", "-jar", "target/producer-1.0.0-shaded.jar"] 