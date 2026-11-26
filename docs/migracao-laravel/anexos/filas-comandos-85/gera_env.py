# variaveis de teste para o ENV_EXTRA do roda-isolado.sh (somam-se ao ambiente que ele gera do ecidade/.env.example;
# vale a ultima): chave, token e enderecos ficticios. Uso: python3 gera_env.py <saida>
import sys,base64
dst=sys.argv[1]
over={'APP_ENV':'testing','APP_KEY':'base64:'+base64.b64encode(b'chave-de-teste-fixa-32-bytes-ok!').decode(),'APP_DEBUG':'true',
 'APP_URL':'http://localhost','DB_HOST':'banco-inexistente.invalid','DB_PASSWORD':'x',
 'MAIL_DRIVER':'array','QUEUE_DRIVER':'sync','CACHE_DRIVER':'array','SESSION_DRIVER':'array','BROADCAST_DRIVER':'log',
 'API_DATA_AVAILABLE_TOKEN':'token-de-teste','API_DATA_AVAILABLE_URL':'http://api.invalid/'}
open(dst,'w').write(''.join(f'{k}={v}\n' for k,v in over.items()))
