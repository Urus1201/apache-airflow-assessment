# Docker & Apache Airflow Assessment

This assessment tests your understanding of Docker containerization and Apache Airflow workflow management through a practical data pipeline project.

## Learning Objectives

By completing this assessment, you will demonstrate your ability to:

1. Configure and optimize Docker containers
2. Understand container networking and volumes
3. Set up and configure Apache Airflow DAGs
4. Implement proper error handling and retry mechanisms
5. Create effective task dependencies in an ETL workflow
6. Integrate services running in different containers

## Assessment Overview

This project contains a data pipeline that:
1. Extracts data about customers, products, and orders from an API
2. Transforms and joins the data
3. Loads the processed data into a SQLite database

The pipeline is implemented as an Apache Airflow DAG and runs in a Docker environment.

## Part 1: Docker Configuration (40 points)

### Task 1: Complete the API Service Dockerfile (15 points)
The API service Dockerfile in `starter/api-services/Dockerfile.incomplete` is missing crucial configuration. You need to:
1. Select an appropriate base image
2. Set up the working directory
3. Install dependencies
4. Configure the entry point

### Task 2: Complete the Docker Compose File (25 points)
The `starter/docker-compose.yml.incomplete` file needs several improvements:
1. Configure healthchecks for the services
2. Set appropriate container restart policies
3. Add environment variables for Airflow configuration
4. Configure volume mounts correctly
5. Add resource constraints to optimize performance

## Part 2: Airflow DAG Development (60 points)

### Task 1: Fix the Extract Task (20 points)
The extract task in the DAG has issues:
1. Implement proper error handling for API failures
2. Add a retry mechanism with exponential backoff
3. Add logging for monitoring and debugging
4. Ensure data validation before proceeding

### Task 2: Optimize the Transform Task (20 points)
The transform task needs improvements:
1. Add data validation to ensure quality
2. Implement more efficient data processing
3. Handle edge cases in the data transformation
4. Add performance metrics collection

### Task 3: Enhance the Load Task (20 points)
The load task needs enhancements:
1. Implement transaction management
2. Add conflict resolution strategy
3. Implement efficient batch loading
4. Add success/failure metrics

## Submission Guidelines

1. Start with the files in the `starter` directory
2. Submit your completed files that address all the tasks
3. Include a brief explanation of your changes and why you made them
4. Test your solution by running the entire pipeline

## Getting Started

1. Copy the files from the `starter` directory to your working directory
2. Follow the tasks described above to complete each component
3. Test your solution using the provided test data
4. Submit your completed files

## Evaluation Criteria

- Correctness: Does the solution work as expected?
- Code quality: Is the code clear, concise, and well-documented?
- Best practices: Does the solution follow Docker and Airflow best practices?
- Error handling: Does the solution handle errors gracefully?
- Performance: Is the solution optimized for performance?

Good luck!