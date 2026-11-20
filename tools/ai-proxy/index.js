// Local-only helper: an OpenAI-compatible /v1/chat/completions endpoint backed by your own
// `wrangler login`, so the harness can call Workers AI from a laptop without an API token.
// Run `npx wrangler dev` in this folder (localhost only). Never deploy it.
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method !== "POST" || !url.pathname.endsWith("/chat/completions")) {
      return new Response("POST /v1/chat/completions only", { status: 404 });
    }
    const { model, messages, max_tokens, temperature, reasoning_effort } = await request.json();
    const input = { messages, max_tokens, temperature };
    if (reasoning_effort) input.reasoning = { effort: reasoning_effort };
    let raw;
    try {
      raw = await env.AI.run(model, input);
    } catch (error) {
      const message = String(error?.message || error);
      const status = /limit|quota|neuron/i.test(message) ? 429 : 502;
      return Response.json({ error: { message } }, { status });
    }
    // Normalise both Workers AI shapes ({response} and OpenAI-style {choices}) to OpenAI.
    const text = raw?.choices?.[0]?.message?.content ?? raw?.response ?? "";
    const usage = raw?.usage ?? {};
    return Response.json({
      id: raw?.id ?? "local",
      object: "chat.completion",
      model,
      choices: [{ index: 0, message: { role: "assistant", content: typeof text === "string" ? text : JSON.stringify(text) }, finish_reason: raw?.choices?.[0]?.finish_reason ?? "stop" }],
      usage: {
        prompt_tokens: usage.prompt_tokens ?? 0,
        completion_tokens: usage.completion_tokens ?? 0,
        total_tokens: usage.total_tokens ?? 0,
        neurons: usage.neurons ?? null,
      },
    });
  },
};
