// Shared test fixtures for shapes that were hand-duplicated across many
// test files.

// Matches the error shape axios rejects with and handleError() expects:
// { response: { data: { data: message } } }
export function mockErrorResponse(message) {
  return {
    response: {
      data: {
        data: message,
      },
    },
  };
}
