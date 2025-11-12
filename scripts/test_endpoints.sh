#!/usr/bin/env bash
# Small integration test script for the API (happy path).
# Requires: curl, jq
# Usage: ./test_endpoints.sh [API_URL]
# Example: ./test_endpoints.sh http://127.0.0.1:8000

set -euo pipefail
API_URL=${1:-http://127.0.0.1:8000}

echo "Using API: $API_URL"

function register() {
  local email=$1; local password=$2; local nombre=$3; local apellido=$4; local rol=$5
  echo "\nRegistering $rol: $email"
  curl -s -X POST "$API_URL/auth/registro" \
    -F "email=$email" \
    -F "password=$password" \
    -F "nombre=$nombre" \
    -F "apellido=$apellido" \
    -F "rol=$rol" | jq .
}

function create_project() {
  local titulo=$1; local descripcion=$2; local estudiante_id=$3; local profesor_id=$4; local fecha_entrega=$5; local nombre_archivo=$6; local comentarios_version=$7
  echo "\nCreating project: $titulo"
  curl -s -X POST "$API_URL/proyectos" \
    -H 'Content-Type: application/json' \
    -d "{\"titulo\":\"$titulo\",\"descripcion\":\"$descripcion\",\"estudiante_id\":$estudiante_id,\"profesor_id\":$profesor_id,\"fecha_entrega\":\"$fecha_entrega\",\"nombre_archivo\":\"$nombre_archivo\",\"comentarios_version\":\"$comentarios_version\"}" | jq .
}

function upload_version() {
  local proyecto_id=$1; local descripcion=$2
  echo "\nUploading version to project $proyecto_id"
  curl -s -X POST "$API_URL/proyectos/$proyecto_id/versiones" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d "descripcion=$descripcion" | jq .
}

function grade_project() {
  local proyecto_id=$1; local profesor_id=$2; local puntaje=$3; local comentarios=$4
  echo "\nGrading project $proyecto_id by profesor $profesor_id"
  curl -s -X POST "$API_URL/calificaciones" \
    -H 'Content-Type: application/json' \
    -d "{\"proyecto_id\":$proyecto_id,\"profesor_id\":$profesor_id,\"puntaje\":$puntaje,\"comentarios\":\"$comentarios\"}" | jq .
}

function get_report() {
  local estudiante_id=$1
  echo "\nGetting report for estudiante $estudiante_id"
  curl -s "$API_URL/reportes/desempeño/estudiante/$estudiante_id" | jq .
}

# Example run (you can edit these values)
STUDENT_EMAIL="est1@example.com"
TEACHER_EMAIL="prof1@example.com"
PASSWORD="secret"

# Register student and professor (manually note the returned id values)
student_json=$(register "$STUDENT_EMAIL" "$PASSWORD" "Estudiante" "Uno" "estudiante")
prof_json=$(register "$TEACHER_EMAIL" "$PASSWORD" "Profesor" "Uno" "profesor")

student_id=$(echo "$student_json" | jq -r '.id')
prof_id=$(echo "$prof_json" | jq -r '.id')

echo "\nRegistered student id: $student_id, professor id: $prof_id"

# Create project
fecha_entrega="2025-12-01T23:59:00"
proj_json=$(create_project "Proyecto Demo" "Descripción de prueba" "$student_id" "$prof_id" "$fecha_entrega" "entrega1.zip" "Primera entrega")
project_id=$(echo "$proj_json" | jq -r '.id')

echo "\nCreated project id: $project_id"

# Upload a new version
upload_version "$project_id" "Segunda versión con correcciones"

# Grade project
grade_project "$project_id" "$prof_id" 4.5 "Buen trabajo"

# Get grades
echo "\nProject grades:"
curl -s "$API_URL/calificaciones/proyecto/$project_id" | jq .

# Get report
get_report "$student_id"

echo "\nDone."
