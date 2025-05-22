#!/bin/bash
#
# Grekko Backup Script
# This script creates backups of Grekko data including database, credentials, and configurations
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BACKUP_TYPE="db"
BACKUP_DIR="./backups"
ENV_FILE=".env.production"
COMPOSE_FILE="docker/docker-compose.prod.yml"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
INCLUDE_LOGS=false

# Print usage
usage() {
  echo -e "${BLUE}Grekko Backup Script${NC}"
  echo -e "Usage: $0 [options]"
  echo -e ""
  echo -e "Options:"
  echo -e "  -t, --type TYPE         Backup type (db, credentials, config, full)"
  echo -e "  -d, --dir DIRECTORY     Directory to store backups"
  echo -e "  -e, --env-file FILE     Environment file location"
  echo -e "  -c, --compose-file FILE Docker Compose file location"
  echo -e "  -l, --logs              Include logs in backup"
  echo -e "  -h, --help              Show this help message"
  exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -t|--type)
      BACKUP_TYPE="$2"
      shift
      shift
      ;;
    -d|--dir)
      BACKUP_DIR="$2"
      shift
      shift
      ;;
    -e|--env-file)
      ENV_FILE="$2"
      shift
      shift
      ;;
    -c|--compose-file)
      COMPOSE_FILE="$2"
      shift
      shift
      ;;
    -l|--logs)
      INCLUDE_LOGS=true
      shift
      ;;
    --full)
      BACKUP_TYPE="full"
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

# Validate backup type
if [[ "$BACKUP_TYPE" != "db" && "$BACKUP_TYPE" != "credentials" && "$BACKUP_TYPE" != "config" && "$BACKUP_TYPE" != "full" ]]; then
  echo -e "${RED}Invalid backup type: $BACKUP_TYPE${NC}"
  echo -e "Valid types are: db, credentials, config, full"
  exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Load environment file if it exists
if [[ -f "$ENV_FILE" ]]; then
  source "$ENV_FILE"
fi

# Set credentials path
CREDENTIALS_PATH=${GREKKO_CREDENTIALS_PATH:-~/.grekko}

# Check if Docker is running
if ! docker ps &> /dev/null; then
  echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
  exit 1
fi

# Check if docker-compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo -e "${RED}Docker Compose file not found: $COMPOSE_FILE${NC}"
  exit 1
fi

# Function to backup database
backup_database() {
  echo -e "${BLUE}Backing up database...${NC}"
  
  # Check if database container is running
  if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q postgres; then
    echo -e "${RED}Database container is not running.${NC}"
    return 1
  fi
  
  # Create backup file
  BACKUP_FILE="$BACKUP_DIR/grekko_db_$TIMESTAMP.sql"
  
  echo -e "Creating database backup: $BACKUP_FILE"
  docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U ${POSTGRES_USER:-grekko} -d ${POSTGRES_DB:-grekko} > "$BACKUP_FILE"
  
  # Compress the backup
  gzip "$BACKUP_FILE"
  
  echo -e "${GREEN}Database backup completed: ${BACKUP_FILE}.gz${NC}"
}

# Function to backup credentials
backup_credentials() {
  echo -e "${BLUE}Backing up credentials...${NC}"
  
  # Check if credentials directory exists
  if [[ ! -d "$CREDENTIALS_PATH" ]]; then
    echo -e "${RED}Credentials directory not found: $CREDENTIALS_PATH${NC}"
    return 1
  fi
  
  # Create backup file
  BACKUP_FILE="$BACKUP_DIR/grekko_credentials_$TIMESTAMP.tar.gz"
  
  echo -e "Creating credentials backup: $BACKUP_FILE"
  tar -czf "$BACKUP_FILE" -C "$(dirname "$CREDENTIALS_PATH")" "$(basename "$CREDENTIALS_PATH")"
  
  echo -e "${GREEN}Credentials backup completed: $BACKUP_FILE${NC}"
  
  # Set secure permissions
  chmod 600 "$BACKUP_FILE"
}

# Function to backup configuration
backup_config() {
  echo -e "${BLUE}Backing up configuration...${NC}"
  
  # Create backup file
  BACKUP_FILE="$BACKUP_DIR/grekko_config_$TIMESTAMP.tar.gz"
  
  echo -e "Creating configuration backup: $BACKUP_FILE"
  tar -czf "$BACKUP_FILE" config/ "$ENV_FILE" docker/*.yml
  
  echo -e "${GREEN}Configuration backup completed: $BACKUP_FILE${NC}"
}

# Function to backup logs
backup_logs() {
  echo -e "${BLUE}Backing up logs...${NC}"
  
  # Create backup file
  BACKUP_FILE="$BACKUP_DIR/grekko_logs_$TIMESTAMP.tar.gz"
  
  echo -e "Creating logs backup: $BACKUP_FILE"
  
  # Check if logs directory exists
  if [[ -d "logs/" ]]; then
    tar -czf "$BACKUP_FILE" logs/
    echo -e "${GREEN}Logs backup completed: $BACKUP_FILE${NC}"
  else
    echo -e "${YELLOW}Logs directory not found, skipping logs backup.${NC}"
  fi
}

# Perform the requested backup
case $BACKUP_TYPE in
  db)
    backup_database
    ;;
  credentials)
    backup_credentials
    ;;
  config)
    backup_config
    ;;
  full)
    backup_database
    backup_credentials
    backup_config
    if [[ "$INCLUDE_LOGS" = true ]]; then
      backup_logs
    fi
    
    # Create a consolidated backup
    FULL_BACKUP_FILE="$BACKUP_DIR/grekko_full_backup_$TIMESTAMP.tar.gz"
    echo -e "${BLUE}Creating full backup archive: $FULL_BACKUP_FILE${NC}"
    tar -czf "$FULL_BACKUP_FILE" "$BACKUP_DIR/grekko_db_$TIMESTAMP.sql.gz" "$BACKUP_DIR/grekko_credentials_$TIMESTAMP.tar.gz" "$BACKUP_DIR/grekko_config_$TIMESTAMP.tar.gz"
    
    if [[ "$INCLUDE_LOGS" = true && -f "$BACKUP_DIR/grekko_logs_$TIMESTAMP.tar.gz" ]]; then
      # Add logs to the full backup
      tar -rf "$FULL_BACKUP_FILE" "$BACKUP_DIR/grekko_logs_$TIMESTAMP.tar.gz"
    fi
    
    echo -e "${GREEN}Full backup completed: $FULL_BACKUP_FILE${NC}"
    
    # Set secure permissions
    chmod 600 "$FULL_BACKUP_FILE"
    ;;
esac

echo -e "${GREEN}Backup process completed successfully.${NC}"
echo -e "Backup files are stored in: ${BLUE}$BACKUP_DIR${NC}"

# Provide backup restoration instructions
echo -e ""
echo -e "${BLUE}Restoration Instructions:${NC}"
if [[ "$BACKUP_TYPE" = "db" || "$BACKUP_TYPE" = "full" ]]; then
  echo -e "To restore database:"
  echo -e "${YELLOW}gunzip -c $BACKUP_DIR/grekko_db_$TIMESTAMP.sql.gz | docker-compose -f $COMPOSE_FILE exec -T postgres psql -U ${POSTGRES_USER:-grekko} -d ${POSTGRES_DB:-grekko}${NC}"
fi

if [[ "$BACKUP_TYPE" = "credentials" || "$BACKUP_TYPE" = "full" ]]; then
  echo -e "To restore credentials:"
  echo -e "${YELLOW}tar -xzf $BACKUP_DIR/grekko_credentials_$TIMESTAMP.tar.gz -C /${NC}"
fi

if [[ "$BACKUP_TYPE" = "config" || "$BACKUP_TYPE" = "full" ]]; then
  echo -e "To restore configuration:"
  echo -e "${YELLOW}tar -xzf $BACKUP_DIR/grekko_config_$TIMESTAMP.tar.gz${NC}"
fi

if [[ "$BACKUP_TYPE" = "full" ]]; then
  echo -e "To restore full backup:"
  echo -e "${YELLOW}tar -xzf $BACKUP_DIR/grekko_full_backup_$TIMESTAMP.tar.gz -C $BACKUP_DIR${NC}"
  echo -e "Then follow the individual restore instructions for each component."
fi

exit 0