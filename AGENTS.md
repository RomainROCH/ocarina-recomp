# Notas para agentes de IA

## Contexto

Leia o [CONTRIBUTING.md](CONTRIBUTING.md): tem o layout do repositório,
as regras, a validação e o método de investigação.

## Convenções específicas

- Nunca edite `generated/` à mão: use `recomp/patches.py` ou
  `tools/oot/patch_generated.py`.

## Verificação

- Execute `python tools/check_content.py` antes de enviar um pull request.
- Se alterar o lifter, execute também os testes em `tests/`.
- Testes abrem janela: use `TOTK_INPUT=none` para o teclado da pessoa não
  mexer no jogo. Siga a validação de `CONTRIBUTING.md`; relate o que foi
  verificado e o que não foi testado.

## Limites

- Nada derivado do jogo entra aqui: executável, código gerado, shaders,
  caches, saves ou dumps. `tools/check_content.py` confere.
- Trabalhe só com a cópia do jogo da própria pessoa. Se ela não tiver, pare.
  Não explique como obter jogo ou keys.
- Não use `--no-verify` nem envie direto para `main`: siga o fluxo de pull
  requests de `CONTRIBUTING.md` e use sua própria identidade do Git.

## Comunicação

Responda em francês neutro e preciso, sem imitar o registro do usuário; preserve
a linguagem do projeto. Apresente resultados, verificações e limites sem
preâmbulos ou repetição. Descobertas secundárias ficam em uma ou duas frases,
salvo quando essenciais ou solicitadas. Preserve a profundidade necessária.
