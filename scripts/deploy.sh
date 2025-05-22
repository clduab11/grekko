#!/bin/bash
#
# Grekko Deployment Script
# This script automates the deployment of Grekko in different environments
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
ACTION="deploy"
SKIP_CONFIRMATION=false
PULL_LATEST=true

# Print usage
usage() {
  echo -e "${BLUE}Grekko Deployment Script${NC}"
  echo -e "Usage: $0 [options]"
  echo -e ""
  echo -e "Options:"
  echo -e "  -e, --environment ENV   Deployment environment (development, testing, production)"
  echo -e "  -a, --action ACTION     Action to perform (deploy, update, restart, stop)"
  echo -e "  -s, --skip-confirmation Skip confirmation prompts"
  echo -e "  --no-pull               Skip pulling latest changes from git"
  echo -e "  -h, --help              Show this help message"
  exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -e|--environment)
      ENVIRONMENT="$2"
      shift
      shift
      ;;
    -a|--action)
      ACTION="$2"
      shift
      shift
      ;;
    -s|--skip-confirmation)
      SKIP_CONFIRMATION=true
      shift
      ;;
    --no-pull)
      PULL_LATEST=false
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      usage
      ;;
  esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "testing" && "$ENVIRONMENT" != "production" ]]; then
  echo -e "${RED}Invalid environment: $ENVIRONMENT${NC}"
  echo -e "Valid environments are: development, testing, production"
  exit 1
fi

# Validate action
if [[ "$ACTION" != "deploy" && "$ACTION" != "update" && "$ACTION" != "restart" && "$ACTION" != "stop" ]]; then
  echo -e "${RED}Invalid action: $ACTION${NC}"
  echo -e "Valid actions are: deploy, update, restart, stop"
  exit 1
fi

# Set environment-specific variables
case $ENVIRONMENT in
  development)
    COMPOSE_FILE="docker/docker-compose.yml"
    ENV_FILE=".env.development"
    WARN_MESSAGE="This will set up a development environment."
    ;;
  testing)
    COMPOSE_FILE="docker/docker-compose.test.yml"
    ENV_FILE=".env.testing"
    WARN_MESSAGE="This will run tests in an isolated environment."
    ;;
  production)
    COMPOSE_FILE="docker/docker-compose.prod.yml"
    ENV_FILE=".env.production"
    WARN_MESSAGE="${RED}WARNING: This will deploy to PRODUCTION environment with REAL FUNDS!${NC}"
    ;;
esac

# Print environment information
echo -e "${BLUE}Grekko Deployment${NC}"
echo -e "Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "Action: ${GREEN}$ACTION${NC}"
echo -e "Compose file: ${GREEN}$COMPOSE_FILE${NC}"
echo -e ""
echo -e "$WARN_MESSAGE"
echo -e ""

# Confirmation
if [[ "$SKIP_CONFIRMATION" = false ]]; then
  if [[ "$ENVIRONMENT" = "production" ]]; then
    read -p "Are you ABSOLUTELY sure you want to continue? (type 'yes' to confirm): " CONFIRM
    if [[ "$CONFIRM" != "yes" ]]; then
      echo -e "${RED}Deployment aborted.${NC}"
      exit 1
    fi
  else
    read -p "Continue? (y/n): " CONFIRM
    if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
      echo -e "${RED}Deployment aborted.${NC}"
      exit 1
    fi
  fi
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
  exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
  echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
  exit 1
fi

# Pull latest changes if enabled
if [[ "$PULL_LATEST" = true ]]; then
  echo -e "${BLUE}Pulling latest changes from git...${NC}"
  git pull
fi

# Check for environment file
if [[ ! -f "$ENV_FILE" && "$ENVIRONMENT" != "development" ]]; then
  if [[ -f "$ENV_FILE.example" ]]; then
    echo -e "${YELLOW}Environment file $ENV_FILE not found, but example file exists.${NC}"
    if [[ "$SKIP_CONFIRMATION" = false ]]; then
      read -p "Create from example? (y/n): " CREATE_ENV
      if [[ "$CREATE_ENV" = "y" || "$CREATE_ENV" = "Y" ]]; then
        cp "$ENV_FILE.example" "$ENV_FILE"
        echo -e "${GREEN}Created $ENV_FILE from example.${NC}"
        echo -e "${YELLOW}Please edit $ENV_FILE with your actual values.${NC}"
        exit 0
      fi
    fi
  else
    echo -e "${RED}Environment file $ENV_FILE not found and no example available.${NC}"
    exit 1
  fi
fi

# Create credentials directory if it doesn't exist
if [[ "$ENVIRONMENT" = "production" ]]; then
  CREDENTIALS_PATH=$(grep GREKKO_CREDENTIALS_PATH "$ENV_FILE" | cut -d= -f2)
  CREDENTIALS_PATH=${CREDENTIALS_PATH:-/var/grekko/credentials}
  
  if [[ ! -d "$CREDENTIALS_PATH" ]]; then
    echo -e "${YELLOW}Credentials directory $CREDENTIALS_PATH doesn't exist.${NC}"
    if [[ "$SKIP_CONFIRMATION" = false ]]; then
      read -p "Create it? (y/n): " CREATE_DIR
      if [[ "$CREATE_DIR" = "y" || "$CREATE_DIR" = "Y" ]]; then
        mkdir -p "$CREDENTIALS_PATH"
        chmod 700 "$CREDENTIALS_PATH"
        echo -e "${GREEN}Created credentials directory $CREDENTIALS_PATH${NC}"
      fi
    fi
  fi
fi

# Perform the requested action
case $ACTION in
  deploy)
    echo -e "${BLUE}Deploying Grekko in $ENVIRONMENT environment...${NC}"
    docker-compose -f "$COMPOSE_FILE" up -d
    ;;
  update)
    echo -e "${BLUE}Updating Grekko in $ENVIRONMENT environment...${NC}"
    docker-compose -f "$COMPOSE_FILE" pull
    docker-compose -f "$COMPOSE_FILE" up -d --build
    ;;
  restart)
    echo -e "${BLUE}Restarting Grekko in $ENVIRONMENT environment...${NC}"
    docker-compose -f "$COMPOSE_FILE" restart
    ;;
  stop)
    echo -e "${BLUE}Stopping Grekko in $ENVIRONMENT environment...${NC}"
    docker-compose -f "$COMPOSE_FILE" down
    ;;
esac

# Check deployment status
if [[ "$ACTION" != "stop" ]]; then
  echo -e "${BLUE}Checking deployment status...${NC}"
  docker-compose -f "$COMPOSE_FILE" ps
fi

echo -e "${GREEN}Action '$ACTION' completed successfully for $ENVIRONMENT environment.${NC}"

# For production, show monitoring instructions
if [[ "$ENVIRONMENT" = "production" ]]; then
  echo -e ""
  echo -e "${BLUE}Monitoring Instructions:${NC}"
  echo -e "1. View logs: ${YELLOW}docker-compose -f $COMPOSE_FILE logs -f grekko-app${NC}"
  echo -e "2. Check metrics: ${YELLOW}http://$(hostname):3000${NC} (if Grafana is configured)"
  echo -e "3. System status: ${YELLOW}docker stats${NC}"
fi

exit 0