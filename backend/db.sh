#!/usr/bin/env bash

# this script checks if the database url is set in .env which overrides the container
# if it is set, we will exit silently, otherwise we will start the container
if [[ -z "$DATABASE_URL" ]]; then
  if ! pnpm run db:status 2>/dev/null | grep -q "trip-itinerary-planner-mongo"; then
    echo "Starting the database container..."
    pnpm run db:up
  fi
else
  echo "DATABASE_URL is set, overiding container skipping the database container..."
fi
