from fastapi.responses import StreamingResponse
from starlette.types import Send


SUCCESS_STATUS_CODE_START = 200
SUCCESS_STATUS_CODE_END = 300

class StreamingResponseWithStatusCode(StreamingResponse):
    """
    Variation of StreamingResponse that can dynamically decide the HTTP status code, based on the returns from the.

    content iterator.

    Expects the content to yield tuples of (content: str, status_code: int).
    The constructor's status_code parameter is ignored but kept for compatibility with StreamingResponse.
    """
    async def stream_response(self, send: Send) -> None:
        """
        A coroutine that streams the response content to the client.

        Parameters:
            send (Send): The coroutine used to send data back to the client.

        Returns:
            None
        """
        content_to_send = ""
        self.status_code = None

        # Initial iterate over the content until a non-empty chunk is found.
        async for chunk_content, chunk_status in self.body_iterator:
            # If a non-empty chunk is encountered, set content to send and possibly the status code.
            if chunk_content:
                content_to_send = chunk_content
                # Only set the status code from the first non-empty chunk.
                if self.status_code is None:
                    self.status_code = chunk_status
                break
            # If an empty chunk has a non-2xx status code, use that status code and end the response.
            if not (SUCCESS_STATUS_CODE_START <= int(chunk_status) < SUCCESS_STATUS_CODE_END):
                self.status_code = chunk_status
                break

        # If no valid status code has been set, default to 200.
        if self.status_code is None:
            self.status_code = 200

        # Send the initial response with the decided status code and send content.
        await self.send_response_start(send)

        if content_to_send:
            await self.send_content(send, content_to_send, more_body=True)

        # Continue streaming the rest of the response.
        async for chunk_content, chunk_status in self.body_iterator:
            if not (SUCCESS_STATUS_CODE_START <= int(chunk_status) < SUCCESS_STATUS_CODE_END):
                self.status_code = chunk_status
                await self.send_content(send, b"", more_body=False)  # End the response if status is not 2xx.
                return
            await self.send_content(send, chunk_content, more_body=True)

        # End the response.
        await self.send_content(send, b"", more_body=False)

    async def send_response_start(self, send: Send) -> None:
        """
        Asynchronous function to send the HTTP response start message.

        Args:
            self: The instance of the class.
            send: The function to send the response.

        Returns:
            None
        """
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": self.raw_headers,
        })

    async def send_content(self, send: Send, content: str, more_body: bool) -> None:  # noqa: FBT001
        """
        Send content asynchronously with the given 'send' function, encoding the content.

        if not already in bytes format.

        Parameters:
        send (Send): The function used to send the content.
        content (str): The content to be sent.
        more_body (bool): Indicates if there is more content to be sent.

        Returns:
        None
        """
        if not isinstance(content, bytes):
            content = content.encode(self.charset)
        await send({
            "type": "http.response.body",
            "body": content,
            "more_body": more_body,
        })
