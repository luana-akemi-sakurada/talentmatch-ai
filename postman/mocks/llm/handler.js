// Local synthetic stand-in for the envelope consumed by llm.py, not a real LLM.
const http = require('http');
http.createServer((req, res) => {
  if (req.method !== 'POST' || req.url !== '/v1/chat/completions') {
    res.writeHead(501, {'content-type': 'application/json'});
    return res.end(JSON.stringify({error: 'Not modeled'}));
  }
  const reply = (status, body) => {res.writeHead(status, {'content-type': 'application/json'});res.end(JSON.stringify(body));};
  const payload = req.body;
  if (!payload || !Array.isArray(payload.messages)) return reply(400, {error: 'Missing messages'});
  const user = payload.messages.find(m => m.role === 'user');
  // Inspect transmitted input without logging its contents.
  if (!user || user.content.includes('Pessoa Fictícia')) return reply(400, {error: 'Privacy check failed'});
  if (payload.model === 'test-unavailable') return reply(503, {error: {message: 'Synthetic provider outage'}});
  const analysis = {habilidades: [{habilidade:'Python', evidencia:'Python SQL'}], anos_experiencia: null,
    evidencia_anos_experiencia:null, experiencia_profissional: [], nota_aderencia: null,
    requisitos_atendidos: [{requisito: 'Python', evidencia: 'Python SQL'}], requisitos_sem_evidencia: []};
  return reply(200, {id:'local-test', object:'chat.completion', created:0, model:payload.model,
    choices:[{index:0, finish_reason:'stop', message:{role:'assistant',content:payload.model === 'test-invalid' ? 'invalid-json' : JSON.stringify(analysis)}}]});
}).listen(process.env.PORT || 4010);
