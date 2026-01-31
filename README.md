# Document Management System (DMS) Backend - Backend Assessment

**Time Limit: 90 minutes**

## Important Instructions

> **1. Fork this repo into your personal github account**
> 
> **2. Do not raise Pull Request in the original repo**
> 
> **3. Application must be runnable with `docker-compose up` command**
> 
> **4. Complete as many APIs as possible within the 60-minute time limit**
> 
> **5. Prioritize working functionality - do not submit broken code that fails to run with `docker-compose up`**

### Tips
- Focus on core functionality first, then add features incrementally
- Test your application with `docker-compose up` before final submission
- A partially complete but working solution is better than a complete but broken one

---

A FastAPI backend project with SQLite database using raw SQL queries (no ORM).

## Objective

Build a backend API for a Document Management System that allows users to manage files and folders in a hierarchical structure, similar to the backend of Google Drive or Dropbox.

## Functional Requirements

### User Authentication
- User registration
- User login with JWT access token
- Multi-user support (each user has their own file/folder hierarchy)

### Folder Management
- Create new folders
- Rename existing folders
- Delete folders (handling non-empty folders appropriately)
- Support for nested folder structures (folders within folders)

### File Management
- Upload files (base64 encoded)
- Download files
- Rename files
- Delete files
- Retrieve file metadata (e.g., name, size, type)
- Move files to different folders

## Required APIs

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login and receive JWT access token |

### Folders (Protected - requires JWT)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/folders` | Create a new folder (payload: `name`, `parent_folder_id`) |
| `GET` | `/folders/{folderId}` | Get folder metadata and list its contents (files and subfolders) |
| `PATCH` | `/folders/{folderId}` | Rename a folder (payload: `name`) |
| `DELETE` | `/folders/{folderId}` | Delete a folder |

### Files (Protected - requires JWT)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/files` | Upload a file (payload: `name`, `content` (base64), `parent_folder_id`) |
| `GET` | `/files/{fileId}` | Get file metadata |
| `GET` | `/files/{fileId}/download` | Download file content |
| `PATCH` | `/files/{fileId}` | Rename a file (payload: `name`) |
| `DELETE` | `/files/{fileId}` | Delete a file |

## Data Models

### User Model
- email
- password

### Folder Model
- name
- user (owner)
- parent folder (can be null)

### File Model
- name
- content (base64 encoded)
- size
- mime type
- user (owner)
- parent folder (can be null)

## Quick Start (Docker)

The easiest way to run the application:

```bash
docker-compose up --build
```

This will:
- Build the Docker image
- Run database migrations automatically
- Start the API server at `http://localhost:8000`

To stop the application:

```bash
docker-compose down
```

## Manual Setup (Without Docker)

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run database migrations

```bash
python migrate.py upgrade
```

### 4. Start the server

```bash
uvicorn app.main:app --reload
```

Or run directly:

```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

## Database Migrations

### Running Migrations

**Apply all pending migrations:**
```bash
python migrate.py upgrade
```

**Revert all migrations:**
```bash
python migrate.py downgrade
```

**List migration status:**
```bash
python migrate.py list
```

## Business Logic Notes

### Folder Deletion
When deleting a folder, you should handle one of the following strategies:
- **Recursive delete**: Delete the folder and all its contents (subfolders and files)
- **Prevent deletion**: Return an error if the folder is not empty
- Document your chosen approach in the API response

### File Upload (Base64)
- Files should be uploaded as base64-encoded strings in the request body
- The server should decode the base64 content and store the binary data
- Calculate and store the file size from the decoded content
- Optionally detect MIME type from file extension or content

### Root Level Items
- Files and folders with `parent_folder_id = NULL` are at the root level
- Each user has their own root level (isolated file systems per user)
