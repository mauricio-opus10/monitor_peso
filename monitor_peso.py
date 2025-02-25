import pandas as pd
import os
import matplotlib.pyplot as plt
import datetime
import numpy as np
from sklearn.linear_model import LinearRegression

# Nome do arquivo CSV
arquivo_csv = "projeto_peso.csv"

# Função para verificar e criar o arquivo inicial


def configurar_projeto():
    if not os.path.exists(arquivo_csv):
        print("Bem-vindo ao monitoramento de peso!")
        print("Vamos configurar o seu projeto de perda ou ganho de peso.")

        while True:
            try:
                data_inicio = input(
                    "Digite a data de início do projeto (formato DD/MM/AAAA): ")
                peso_inicio = float(
                    input("Digite o peso inicial (kg): ").replace(",", "."))

                # Valida e converte a data inicial
                data_inicio_dt = datetime.datetime.strptime(
                    data_inicio, "%d/%m/%Y")

                # Solicita e valida a data final
                while True:
                    data_fim = input(
                        "Digite a data final do projeto (formato DD/MM/AAAA): ")
                    try:
                        data_fim_dt = datetime.datetime.strptime(
                            data_fim, "%d/%m/%Y")

                        if data_fim_dt <= data_inicio_dt:
                            print(
                                "Erro: A data final deve ser posterior à data inicial. Tente novamente.")
                        else:
                            break  # Data final válida
                    except ValueError:
                        print("Erro: Formato de data inválido. Use DD/MM/AAAA.")

                peso_desejado = float(
                    input("Digite o peso desejado ao final do projeto (kg): ").replace(",", "."))

                # Confirma os dados antes de salvar
                print(f"\nConfirme os dados do projeto:")
                print(
                    f"Data de início: {data_inicio} | Peso inicial: {peso_inicio}kg")
                print(
                    f"Data de fim: {data_fim} | Peso desejado: {peso_desejado}kg")
                confirmacao = input(
                    "Os dados estão corretos? Digite 'S' para confirmar ou 'N' para corrigir: ").strip().upper()

                if confirmacao == "S":
                    # Converte as datas para o formato padrão e salva no CSV
                    data_inicio_formatada = data_inicio_dt.strftime("%Y-%m-%d")
                    data_fim_formatada = data_fim_dt.strftime("%Y-%m-%d")

                    dados_iniciais = pd.DataFrame(
                        [[data_inicio_formatada, peso_inicio], [
                            data_fim_formatada, peso_desejado]],
                        columns=["Data", "Peso"]
                    )
                    dados_iniciais.to_csv(arquivo_csv, index=False)
                    print("Projeto configurado com sucesso!")
                    print("Agora você pode começar a registrar seus pesos semanais.")
                    break
                else:
                    print(
                        "Configuração cancelada. Por favor, insira os dados novamente.")
            except ValueError:
                print("Erro: Formato de data ou peso inválido. Tente novamente.")
    else:
        print("Arquivo de projeto encontrado. Vamos continuar o monitoramento!")

# Função para obter a data inicial e final do projeto a partir do CSV


def obter_datas_projeto():
    historico = pd.read_csv(arquivo_csv, sep=",")
    data_inicio = pd.to_datetime(historico.iloc[0]["Data"])
    data_fim = pd.to_datetime(historico.iloc[-1]["Data"])
    return data_inicio, data_fim

# Função para registrar ou atualizar um peso


def registrar_peso(data, peso):
    historico = pd.read_csv(arquivo_csv, sep=",")
    data_inicio, data_fim = obter_datas_projeto()

    # Converte a data fornecida para o formato padrão ISO
    try:
        data_formatada = datetime.datetime.strptime(
            data, "%d/%m/%Y").strftime("%Y-%m-%d")
        data_formatada_dt = pd.to_datetime(data_formatada)
    except ValueError:
        print("Erro: Formato de data inválido. Use DD/MM/AAAA.")
        return

    # Verifica se a data está no intervalo do projeto
    if not (data_inicio <= data_formatada_dt <= data_fim):
        print(
            f"Erro: A data {data} está fora do período do projeto ({data_inicio.date()} a {data_fim.date()}).")
        return

    # Verifica se a data já existe no histórico
    if data_formatada in historico["Data"].values:
        print(f"A data {data} já está registrada no histórico.")
        escolha = input(
            "Deseja atualizar o peso dessa data? Digite 'S' para sim ou 'N' para não: ").strip().upper()

        if escolha == "S":
            # Atualiza o peso da data existente
            historico.loc[historico["Data"] == data_formatada, "Peso"] = peso
            historico.to_csv(arquivo_csv, index=False)
            print(
                f"O peso da data {data} foi atualizado para {peso}kg com sucesso!")
        else:
            print("Operação cancelada. Nenhuma alteração foi feita.")
    else:
        # Adiciona o novo registro ao histórico
        novo_registro = pd.DataFrame(
            [[data_formatada, peso]], columns=["Data", "Peso"])
        historico = pd.concat([historico, novo_registro], ignore_index=True)
        historico = historico.sort_values("Data")  # Ordena por data
        historico.to_csv(arquivo_csv, index=False)
        print(f"Peso de {peso} kg registrado com sucesso para a data {data}!")

# Função para analisar o progresso


def analisar_progresso():
    historico = pd.read_csv(arquivo_csv, sep=",")  # Lê o histórico
    data_inicio, data_fim = obter_datas_projeto()

    # Valida e converte as datas
    historico["Data"] = pd.to_datetime(
        historico["Data"], format="%Y-%m-%d", errors="coerce")

    # Detecta e avisa sobre erros no arquivo
    if historico["Data"].isnull().any():
        print(
            "Algumas datas no histórico estão inválidas. Verifique e corrija manualmente!")
        print(historico[historico["Data"].isnull()])
        return

    # Verifica se há registros suficientes
    if len(historico) < 3:  # Exige pelo menos dois registros, além das datas inicial e final
        print(
            "É necessário pelo menos dois registros intermediários para realizar a análise.")
        return

    historico = historico.sort_values("Data")  # Ordena por data

    # Criando eixo X (tempo) e Y (peso)
    dias = (historico["Data"] - historico["Data"].min()
            ).dt.days.values.reshape(-1, 1)
    pesos = historico["Peso"].values.reshape(-1, 1)

    # Regressão linear para prever data do peso-alvo
    modelo = LinearRegression()
    modelo.fit(dias, pesos)

    # Projeção da meta
    # Última linha contém o peso desejado
    peso_desejado = historico.iloc[-1]["Peso"]
    dias_para_meta = (
        peso_desejado - modelo.intercept_[0]) / modelo.coef_[0][0]
    data_prevista = historico["Data"].min(
    ) + pd.to_timedelta(dias_para_meta, unit="D")
    data_prevista_formatada = data_prevista.strftime(
        "%d/%m/%Y")  # Formata a data para DD/MM/AAAA

    print(
        f"Se continuar nesse ritmo, você atingirá {peso_desejado}kg em: {data_prevista_formatada}")

    # Projeção no gráfico
    dias_projetados = np.arange(0, int(dias_para_meta) + 1).reshape(-1, 1)
    pesos_projetados = modelo.predict(dias_projetados)

    # Criando gráfico
    plt.figure(figsize=(10, 6))
    plt.plot(historico["Data"], historico["Peso"],
             marker="o", linestyle="-", label="Peso atual")
    plt.axhline(y=peso_desejado, color="r", linestyle="--",
                label=f"Meta {peso_desejado}kg")

    # Adicionando projeção
    datas_projetadas = [historico["Data"].min() + pd.Timedelta(days=int(d))
                        for d in dias_projetados]
    plt.plot(datas_projetadas, pesos_projetados,
             linestyle="--", color="blue", label="Projeção")

    # Texto para a previsão
    texto_previsao = f"Previsão de chegar em sua meta em {data_prevista_formatada}"

    # Exibe a legenda principal
    plt.legend(loc="upper right", title=texto_previsao, frameon=True)

    # Configuração do gráfico
    plt.xlabel("Data")
    plt.ylabel("Peso (kg)")
    plt.title("Evolução do Peso com Projeção")
    plt.grid()

    # Exibe o gráfico
    plt.show()


# Fluxo principal
if __name__ == "__main__":
    configurar_projeto()
    while True:
        print("\n1 - Registrar peso\n2 - Analisar progresso\n3 - Sair")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            data = input("Digite a data do registro (formato DD/MM/AAAA): ")
            try:
                peso = float(input("Digite o peso (kg): ").replace(",", "."))
            except ValueError:
                print("Erro: Peso inválido. Use apenas números.")
                continue
            registrar_peso(data, peso)
        elif opcao == "2":
            analisar_progresso()
        elif opcao == "3":
            print("Saindo... Até mais!")
            break
        else:
            print("Opção inválida, tente novamente.")
