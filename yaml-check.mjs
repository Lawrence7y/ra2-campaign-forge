import yaml from 'js-yaml'
import { readFileSync } from 'node:fs'
const text = readFileSync('C:/Users/Administrator/.dsh/profiles/desktop/cordis.patch.yml', 'utf8')
try {
  const doc = yaml.load(text, { schema: yaml.CORE_SCHEMA })
  const arr = Array.isArray(doc) ? doc : []
  const ids = arr.filter(e => e && typeof e === 'object' && 'id' in e).map(e => String(e.id))
  console.log('YAML_OK entries=' + arr.length)
  console.log('has tool-subagent: ' + ids.includes('tool-subagent'))
  const ts = arr.find(e => e && e.id === 'tool-subagent')
  console.log('tool-subagent config: ' + JSON.stringify(ts && ts.config))
  console.log('has agent-team: ' + ids.includes('agent-team') + ', tool-agent-team: ' + ids.includes('tool-agent-team'))
} catch (e) {
  console.log('YAML_FAIL ' + e.message.split('\n')[0])
}