from flask import Flask, render_template, request, redirect, url_for, flash
from banco import conectar
from datetime import date

app = Flask(__name__)
app.secret_key = "troque-esta-chave-em-um-projeto-real"


def consultar(sql, valores=(), todos=True):
    conn = conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, valores)
            resultado = cur.fetchall() if todos else None
        return resultado
    finally:
        conn.close()


def executar(sql, valores=()):
    conn = conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, valores)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.route("/")
def inicio():
    try:
        totais = {
            "alunos": consultar("SELECT COUNT(*) FROM aluno")[0][0],
            "acompanhantes": consultar("SELECT COUNT(*) FROM acompanhante")[0][0],
            "aulas": consultar("SELECT COUNT(*) FROM aula")[0][0],
            "atividades": consultar("SELECT COUNT(*) FROM atividade")[0][0],
        }
    except Exception:
        totais = {"alunos": 0, "acompanhantes": 0, "aulas": 0, "atividades": 0}
        flash("Confira se o banco de dados foi criado e configurado. Veja o arquivo README.txt.", "aviso")
    return render_template("index.html", totais=totais)


@app.route("/aluno", methods=["GET", "POST"])
def aluno():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cpf = request.form.get("cpf", "").strip()
        if not nome or not cpf:
            flash("Preencha o nome e o CPF do aluno.", "erro")
        else:
            try:
                idade = request.form.get("idade") or None
                executar(
                    """INSERT INTO aluno (nome, cpf, idade, telefone, cidade, nivel)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (nome, cpf, idade, request.form.get("telefone", "").strip() or None,
                     request.form.get("cidade", "").strip() or None,
                     request.form.get("nivel", "").strip() or None)
                )
                flash("Aluno cadastrado com sucesso!", "sucesso")
                return redirect(url_for("aluno"))
            except Exception as e:
                flash("Não foi possível cadastrar. Confira se o CPF já está cadastrado e se o banco está configurado.", "erro")
    lista = consultar("SELECT id, nome, cpf, idade, telefone, cidade, nivel FROM aluno ORDER BY nome")
    return render_template("alunos.html", alunos=lista)


@app.route("/acompanhante", methods=["GET", "POST"])
def acompanhante():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        if not nome:
            flash("Preencha o nome do acompanhante.", "erro")
        else:
            try:
                executar("""INSERT INTO acompanhante (nome, telefone, email, instituto, funcao)
                            VALUES (%s, %s, %s, %s, %s)""",
                         (nome, request.form.get("telefone", "").strip() or None,
                          request.form.get("email", "").strip() or None,
                          request.form.get("instituto", "").strip() or None,
                          request.form.get("funcao", "").strip() or None))
                flash("Acompanhante cadastrado com sucesso!", "sucesso")
                return redirect(url_for("acompanhante"))
            except Exception:
                flash("Não foi possível cadastrar o acompanhante. Confira a configuração do banco.", "erro")
    lista = consultar("SELECT id, nome, telefone, email, instituto, funcao FROM acompanhante ORDER BY nome")
    return render_template("acompanhantes.html", acompanhantes=lista)


@app.route("/aulas", methods=["GET", "POST"])
def aulas():
    if request.method == "POST":
        try:
            executar("""INSERT INTO aula (aluno_id, acompanhante_id, data_aula, tema, observacao)
                        VALUES (%s, %s, %s, %s, %s)""",
                     (request.form.get("aluno_id"), request.form.get("acompanhante_id"),
                      request.form.get("data_aula"), request.form.get("tema", "").strip(),
                      request.form.get("observacao", "").strip() or None))
            flash("Aula registrada com sucesso!", "sucesso")
            return redirect(url_for("aulas"))
        except Exception:
            flash("Não foi possível registrar. Cadastre primeiro um aluno e um acompanhante e confira os campos.", "erro")
    aluno_lista = consultar("SELECT id, nome FROM aluno ORDER BY nome")
    acompanhante_lista = consultar("SELECT id, nome FROM acompanhante ORDER BY nome")
    lista = consultar("""SELECT a.id, al.nome, ac.nome, a.data_aula, a.tema, a.observacao
                         FROM aula a JOIN aluno al ON al.id = a.aluno_id
                         JOIN acompanhante ac ON ac.id = a.acompanhante_id
                         ORDER BY a.data_aula DESC, a.id DESC""")
    return render_template("aulas.html", alunos=aluno_lista, acompanhantes=acompanhante_lista, aulas=lista, hoje=date.today().isoformat())


@app.route("/atividade", methods=["GET", "POST"])
def atividade():
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        if not titulo:
            flash("Preencha o título da atividade.", "erro")
        else:
            try:
                executar("INSERT INTO atividade (titulo, descricao, tipo, nivel) VALUES (%s, %s, %s, %s)",
                         (titulo, request.form.get("descricao", "").strip() or None,
                          request.form.get("tipo", "").strip() or None,
                          request.form.get("nivel", "").strip() or None))
                flash("Atividade cadastrada com sucesso!", "sucesso")
                return redirect(url_for("atividade"))
            except Exception:
                flash("Não foi possível cadastrar a atividade. Confira a configuração do banco.", "erro")
    lista = consultar("SELECT id, titulo, descricao, tipo, nivel FROM atividade ORDER BY titulo")
    return render_template("atividades.html", atividades=lista)


@app.route("/progresso", methods=["GET", "POST"])
def progresso():
    if request.method == "POST":
        try:
            executar("""INSERT INTO progresso (aluno_id, atividade_id, data_registro, resultado, observacao)
                        VALUES (%s, %s, %s, %s, %s)""",
                     (request.form.get("aluno_id"), request.form.get("atividade_id"),
                      request.form.get("data_registro"), request.form.get("resultado"),
                      request.form.get("observacao", "").strip() or None))
            flash("Progresso registrado com sucesso!", "sucesso")
            return redirect(url_for("progresso"))
        except Exception:
            flash("Não foi possível registrar. Confira se há aluno e atividade cadastrados e se os campos estão preenchidos.", "erro")
    aluno_lista = consultar("SELECT id, nome FROM aluno ORDER BY nome")
    atividade_lista = consultar("SELECT id, titulo FROM atividade ORDER BY titulo")
    lista = consultar("""SELECT p.id, al.nome, at.titulo, p.data_registro, p.resultado, p.observacao
                         FROM progresso p JOIN aluno al ON al.id = p.aluno_id
                         JOIN atividade at ON at.id = p.atividade_id
                         ORDER BY p.data_registro DESC, p.id DESC""")
    return render_template("progresso.html", alunos=aluno_lista, atividades=atividade_lista, progressos=lista, hoje=date.today().isoformat())


if __name__ == "__main__":
    app.run(debug=True)
