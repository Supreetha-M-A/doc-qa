import { useRef, useState } from 'react';

type Msg = { role: 'user' | 'assistant'; content: string };

export default function App() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  async function send() {
    const text = input.trim();
    if (!text || streaming) return;

    const next: Msg[] = [...messages, { role: 'user', content: text }];

    // Push an empty assistant message BEFORE the request starts, so the UI has
    // somewhere to stream into and the user sees a response begin immediately.
    setMessages([...next, { role: 'assistant', content: '' }]);
    setInput('');
    setStreaming(true);
    setError(null);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: next }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status} at ${res.url}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // stream:true matters — a multi-byte character can be split across
        // two chunks, and without it you get occasional corrupted text.
        const chunk = decoder.decode(value, { stream: true });

        setMessages((prev) => {
          const copy = [...prev];
          const last = copy[copy.length - 1];
          copy[copy.length - 1] = { ...last, content: last.content + chunk };
          return copy;
        });
      }
    } catch (e) {
      // The user pressing Stop is not an error.
      if ((e as Error).name !== 'AbortError') {
        setError(`Request failed: ${(e as Error).message}`);
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: '2rem auto', fontFamily: 'system-ui', lineHeight: 1.5 }}>
      <h1>doc-qa</h1>

      <div aria-live="polite">
        {messages.length === 0 && !streaming && <p>Ask something to start.</p>}
        {messages.map((m, i) => (
          <p key={i}>
            <strong>{m.role === 'user' ? 'You' : 'Assistant'}:</strong>{' '}
            {m.content}
            {streaming && i === messages.length - 1 && !m.content && '…'}
          </p>
        ))}
      </div>

      {error && <p role="alert" style={{ color: 'crimson' }}>{error}</p>}

      <form onSubmit={(e) => { e.preventDefault(); send(); }}>
        <label htmlFor="prompt">Message</label>{' '}
        <input
          id="prompt"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={streaming}
          style={{ width: '60%' }}
        />{' '}
        <button type="submit" disabled={streaming || !input.trim()}>Send</button>{' '}
        {streaming && <button type="button" onClick={() => abortRef.current?.abort()}>Stop</button>}
      </form>
    </main>
  );
}