// Compatibilidad: la fuente editable es ahora LaTeX, no HTML.
const {spawnSync}=require('node:child_process');
const path=require('node:path');
const result=spawnSync('bash',[path.join(__dirname,'compilar_documentos.sh')],{stdio:'inherit'});
process.exit(result.status ?? 1);
