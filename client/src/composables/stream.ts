export const useStream = async <T>(
  url: string,
  data: T,
  callback: (data: string) => any,
  options?: RequestInit,
): Promise<void> => {
  const response = await fetch(url, {
    ...options,
    method: "POST",
    body: JSON.stringify(data),
    headers: { "Content-Type": "application/json" },
  });

  if (!response.body) {
    throw new Error("No response body");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    let lines = buffer.split('\n');

    for (let i = 0; i < lines.length - 1; i++) {
      const line = lines[i].replace(/^data: /, '').trim();
      if (line && line !== '[DONE]') {
        callback(line + '\n');
      }
    }

    buffer = lines[lines.length - 1];
  }

  if (buffer) {
    const line = buffer.replace(/^data: /, '').trim();
    if (line && line !== '[DONE]') {
      callback(line + '\n');
    }
  }
};
