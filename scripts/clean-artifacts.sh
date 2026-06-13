#!/usr/bin/env bash
# clean-artifacts.sh — higiene SOB DEMANDA dos artefatos não-versionados do projeto.
#
# Poda: transcripts de sessão do Claude Code (~/.claude/projects/<slug>/*.jsonl) com mais de
#       N dias (default 7), SEMPRE preservando a sessão ativa (a mais recente); e o conteúdo
#       de tmp/ no repo (scratch).
# NUNCA toca em memory/ nem em artefatos versionados — a memória se higieniza por REVISÃO
# (dedup/remover obsoleto/validar contra o repo), nunca por deleção em lote.
#
# Uso:
#   scripts/clean-artifacts.sh            # dry-run: só lista o que seria apagado
#   scripts/clean-artifacts.sh --force    # apaga de fato
#   scripts/clean-artifacts.sh --days=14  # muda a janela de retenção (default 7)
set -euo pipefail

DAYS=7
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --days=*) DAYS="${arg#--days=}" ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "argumento desconhecido: $arg" >&2; exit 2 ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SLUG="$(printf '%s' "$REPO_ROOT" | sed 's#/#-#g')"   # /home/x/y -> -home-x-y (slug do Claude)
SESSIONS_DIR="$HOME/.claude/projects/$SLUG"
TMP_DIR="$REPO_ROOT/tmp"

mode="DRY-RUN (nada será apagado; use --force para executar)"
[ "$FORCE" -eq 1 ] && mode="FORCE (apagando de fato)"
echo "🧹 clean-artifacts — $mode | retenção: $DAYS dias"
echo "   repo:    $REPO_ROOT"
echo "   sessões: $SESSIONS_DIR"

remove() {  # $1 = caminho a remover
  if [ "$FORCE" -eq 1 ]; then
    rm -rf -- "$1" && echo "   apagado:        $1"
  else
    echo "   [seria apagado] $1"
  fi
}

# 1) Transcripts de sessão antigos (preserva a sessão ativa = .jsonl mais recente)
if [ -d "$SESSIONS_DIR" ]; then
  active_jsonl="$(ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null | head -1 || true)"
  active_id=""
  [ -n "$active_jsonl" ] && active_id="$(basename "$active_jsonl" .jsonl)"
  echo "   sessão ativa preservada: ${active_id:-<nenhuma>}"
  found=0
  while IFS= read -r -d '' entry; do
    name="$(basename "$entry")"
    case "$name" in
      memory) continue ;;                         # blindagem: nunca a memória
      "$active_id" | "$active_id".jsonl) continue ;;  # blindagem: nunca a sessão ativa
    esac
    remove "$entry"
    found=1
  done < <(find "$SESSIONS_DIR" -mindepth 1 -maxdepth 1 -mtime +"$DAYS" ! -name memory -print0)
  [ "$found" -eq 0 ] && echo "   (nenhum transcript com mais de $DAYS dias)"
else
  echo "   (diretório de sessões não existe — nada a podar)"
fi

# 2) Scratch tmp/ do repo
if [ -d "$TMP_DIR" ] && [ -n "$(ls -A "$TMP_DIR" 2>/dev/null)" ]; then
  while IFS= read -r -d '' entry; do
    remove "$entry"
  done < <(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -print0)
else
  echo "   (tmp/ vazio ou inexistente)"
fi

echo "✅ fim."
