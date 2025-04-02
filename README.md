# QNXtainer Server

The runtime and image builder for QNXtainer, a container runtime for QNX systems.

## Development

### Prerequisites

- Python 3.10+
- QNX SDP 8.0 (for QNX-specific functionality)
- uv (for image builder)

### Getting Started

1. Clone the repository
2. Install image builder dependencies:
   ```bash
   cd image_builder
   uv sync
   ```
3. Copy the server directory contents onto the QNX system.
   TODO: Figure out a unified way to do this.

4. Build the `cpp-demo-app` image:

   ```bash
   cd image_builder
   uv run image_builder.py ../cpp-demo-app
   ```

5. Deploy the resulting tarball (should be in ~/.qnxtainer/images/) onto your QNX system with QNXtainer Studio.

## Project Structure

- `server/` - QNXtainer runtime and REST API
- `image_builder/` - Image builder script and dependencies
- `public/` - Static assets
- `api_client/` - API client for QNX container management

## License

MIT

## Acknowledgements

- QNX is a registered trademark of BlackBerry Limited
- This project is not officially affiliated with QNX Software Systems Limited or BlackBerry Limited
