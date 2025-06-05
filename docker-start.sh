#!/bin/bash

# Ink2MD Docker Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to start production environment
start_production() {
    local domain=${1:-localhost}
    print_status "Starting Ink2MD in production mode with domain: $domain..."
    HOST_DOMAIN=$domain docker compose up -d
    
    if [ $? -eq 0 ]; then
        print_success "Ink2MD is now running!"
        echo ""
        echo "🌐 Frontend: http://$domain:3000"
        echo "🔧 Backend API: http://$domain:6201"
        echo ""
        echo "To view logs: docker compose logs -f"
        echo "To stop: docker compose down"
    else
        print_error "Failed to start Ink2MD"
        exit 1
    fi
}

# Function to start development environment
start_development() {
    local domain=${1:-localhost}
    print_status "Starting Ink2MD in development mode with domain: $domain..."
    HOST_DOMAIN=$domain docker compose -f docker-compose.dev.yml up -d
    
    if [ $? -eq 0 ]; then
        print_success "Ink2MD development environment is now running!"
        echo ""
        echo "🌐 Frontend (with hot-reload): http://$domain:5173"
        echo "🔧 Backend API: http://$domain:6201"
        echo ""
        echo "To view logs: docker compose -f docker-compose.dev.yml logs -f"
        echo "To stop: docker compose -f docker-compose.dev.yml down"
    else
        print_error "Failed to start Ink2MD development environment"
        exit 1
    fi
}

# Function to stop all environments
stop_all() {
    print_status "Stopping all Ink2MD environments..."
    
    # Stop production
    if docker compose ps -q > /dev/null 2>&1; then
        print_status "Stopping production environment..."
        docker compose down
    fi
    
    # Stop development
    if docker compose -f docker-compose.dev.yml ps -q > /dev/null 2>&1; then
        print_status "Stopping development environment..."
        docker compose -f docker-compose.dev.yml down
    fi
    
    print_success "All Ink2MD environments stopped"
}

# Function to show status
show_status() {
    print_status "Ink2MD Environment Status:"
    echo ""
    
    echo "Production Environment:"
    if docker compose ps -q > /dev/null 2>&1 && [ -n "$(docker compose ps -q)" ]; then
        docker compose ps
    else
        echo "  Not running"
    fi
    
    echo ""
    echo "Development Environment:"
    if docker compose -f docker-compose.dev.yml ps -q > /dev/null 2>&1 && [ -n "$(docker compose -f docker-compose.dev.yml ps -q)" ]; then
        docker compose -f docker-compose.dev.yml ps
    else
        echo "  Not running"
    fi
}

# Function to rebuild and start
rebuild() {
    local env="$1"
    local domain="${2:-localhost}"
    print_status "Rebuilding and starting Ink2MD..."
    
    if [ "$env" = "dev" ]; then
        docker compose -f docker-compose.dev.yml down
        HOST_DOMAIN=$domain docker compose -f docker-compose.dev.yml up -d --build
        print_success "Development environment rebuilt and started with domain: $domain!"
    else
        docker compose down
        HOST_DOMAIN=$domain docker compose up -d --build
        print_success "Production environment rebuilt and started with domain: $domain!"
    fi
}

# Function to show help
show_help() {
    echo "Ink2MD Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND] [build] [DOMAIN]"
    echo ""
    echo "Commands:"
    echo "  start, prod [build] [domain]  Start production environment with optional domain/IP (default: localhost)"
    echo "  dev [build] [domain]          Start development environment with optional domain/IP (default: localhost)"
    echo "  stop                  Stop all environments"
    echo "  status                Show status of all environments"
    echo "  rebuild [build] [dev] [domain] Rebuild and start (add 'dev' for development, optional domain/IP)"
    echo "  logs [build] [dev]    Show logs (add 'dev' for development)"
    echo "  help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start production with localhost"
    echo "  $0 start example.com        # Start production with custom domain"
    echo "  $0 start build example.com  # Start production with custom domain (with build flag)"
    echo "  $0 dev 192.168.1.100        # Start development with IP address"
    echo "  $0 dev pdf2md.local         # Start development with custom domain"
    echo "  $0 dev build pdf2md.local   # Start development with custom domain (with build flag)"
    echo "  $0 rebuild dev              # Rebuild development environment with localhost"
    echo "  $0 rebuild dev example.com  # Rebuild development with custom domain"
    echo "  $0 rebuild build dev example.com # Rebuild development with custom domain (with build flag)"
    echo "  $0 logs                    # Show production logs"
    echo "  $0 logs dev                # Show development logs"
    echo "  $0 logs build dev          # Show development logs (with build flag)"
}

# Function to show logs
show_logs() {
    if [ "$1" = "dev" ]; then
        print_status "Showing development environment logs..."
        docker compose -f docker-compose.dev.yml logs -f
    else
        print_status "Showing production environment logs..."
        docker compose logs -f
    fi
}

# Main script logic
check_docker

case "${1:-help}" in
    "start"|"prod")
        # Check if the second parameter is "build"
        if [ "$2" = "build" ]; then
            # Use the third parameter as the domain
            start_production "$3"
        else
            # Use the second parameter as the domain
            start_production "$2"
        fi
        ;;
    "dev")
        # Check if the second parameter is "build"
        if [ "$2" = "build" ]; then
            # Use the third parameter as the domain
            start_development "$3"
        else
            # Use the second parameter as the domain
            start_development "$2"
        fi
        ;;
    "stop")
        stop_all
        ;;
    "status")
        show_status
        ;;
    "rebuild")
        # Check if the second parameter is "build"
        if [ "$2" = "build" ]; then
            # Use the third parameter as the environment and the fourth parameter as the domain
            rebuild "$3" "$4"
        else
            # Use the second parameter as the environment and the third parameter as the domain
            rebuild "$2" "$3"
        fi
        ;;
    "logs")
        # Check if the second parameter is "build"
        if [ "$2" = "build" ]; then
            # Use the third parameter as the environment
            show_logs "$3"
        else
            # Use the second parameter as the environment
            show_logs "$2"
        fi
        ;;
    "help"|*)
        show_help
        ;;
esac
