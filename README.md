# Short Link Service

A Flask HTTP service that converts long URLs into short codes, redirects users to the original URL, and tracks how many times each short link has been followed.

## Features

- Create a short link from a valid HTTP/HTTPS URL
- Redirect short codes to their original URLs
- Track redirect counts
- Reject malformed URLs with HTTP 400
- Return HTTP 404 for unknown short codes
- Return the same short code when the same URL is submitted again
- Persist links using SQLite

## API

### Create a link

`POST /links`

Request:

```json
{
  "url": "https://example.com"
}