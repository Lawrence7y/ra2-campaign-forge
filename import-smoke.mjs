import('file:///C:/Users/Administrator/.dsh/profiles/desktop/node_modules/@deepseek-ai/dsh-experimental-agent-team/lib/index.js')
  .then(m => { console.log('agent-team import OK; exports=' + Object.keys(m).join(',')) })
  .catch(e => { console.log('IMPORT_FAIL ' + e.message.split('\n')[0]) })