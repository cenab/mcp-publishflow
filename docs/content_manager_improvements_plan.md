# Plan for ContentManager Improvements

Here is a detailed plan for further improvements to the `ContentManager` class and related aspects:

## Recommended Improvements:

1.  **Introduce Asynchronous Operations:** The current implementation uses blocking `requests` calls for image processing and broken link checking. For better performance and scalability, especially in a server environment, these operations could be made asynchronous using libraries like `asyncio` and `aiohttp`.
2.  **Enhance Configuration Management:** While settings are used, consider implementing dependency injection for the `settings` object. This would make the `ContentManager` class easier to test and manage its dependencies explicitly.
3.  **Strengthen Test Coverage:** Review and expand the unit tests for the `ContentManager`, particularly for the newly added features like broken link validation and social media message truncation. Ensure comprehensive test cases cover various scenarios, including edge cases and error conditions.
4.  **Adopt a Dedicated Markdown Library:** Using regular expressions for parsing markdown can be fragile. Integrating a robust markdown parsing library (e.g., `markdown-it-py`, `mistune`) would provide more reliable parsing of frontmatter, links, and other markdown elements.
5.  **Improve Image Handling Robustness:** Add validation for image formats and sizes before uploading. Consider supporting other image embedding methods like base64.
6.  **Refine Logging:** Review logging levels and messages to ensure they provide sufficient detail for monitoring and debugging without being overly verbose.
7.  **Review Docstrings and Type Hinting:** Ensure all methods, parameters, return types, and exceptions are accurately and clearly documented, especially after the recent modifications.

## Implementation Plan:

*   **Step 1: Implement Asynchronous HTTP Requests:**
    *   Modify `_process_single_image` and the broken link check in `validate_content` to use an asynchronous HTTP library (`aiohttp`).
    *   Update the calling methods (`process_images`, `validate_content`) and potentially `process_markdown` to be asynchronous (`async def`).
    *   This will likely require changes in how these methods are called from the main application.
*   **Step 2: Implement Dependency Injection for Settings:**
    *   Modify the `ContentManager` constructor to accept a settings object.
    *   Update the instantiation of `ContentManager` in the application to pass the settings.
*   **Step 3: Expand Unit Tests:**
    *   Write new test cases for broken link validation in `test_mcp_publish_server.py`.
    *   Add tests for the social media message truncation logic.
    *   Ensure existing tests are updated or still valid after the changes.
*   **Step 4: Integrate a Markdown Parsing Library:**
    *   Choose a suitable markdown library.
    *   Replace the regex-based frontmatter parsing and link finding with the library's functionality.
    *   Update `parse_frontmatter` and `validate_content`.
*   **Step 5: Add Image Validation:**
    *   Implement checks for image format and size in `_process_single_image` before uploading.
    *   Consider adding support for base64 encoded images if needed.
*   **Step 6: Refine Logging and Documentation:**
    *   Review all logging statements for clarity and appropriate levels.
    *   Update docstrings and type hints to reflect the current implementation.

```mermaid
graph TD
    A[Start] --> B{Review Current Code};
    B --> C[Identify Areas for Improvement];
    C --> D[Plan Implementation Steps];
    D --> E[Implement Asynchronous Operations];
    E --> F[Implement Dependency Injection];
    F --> G[Expand Unit Tests];
    G --> H[Integrate Markdown Library];
    H --> I[Add Image Validation];
    I --> J[Refine Logging and Docs];
    J --> K[Final Review];
    K --> L[Attempt Completion];