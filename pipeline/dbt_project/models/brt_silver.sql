{{
    config(
        materialized='view'
    )
}}

SELECT 
    codigo,
    placa,
    linha,
    SAFE_CAST(latitude AS FLOAT64) AS latitude,
    SAFE_CAST(longitude AS FLOAT64) AS longitude,
    DATETIME(SAFE.TIMESTAMP_MILLIS(SAFE_CAST(dataHora AS INT64)), 'America/Sao_Paulo') AS datahora_emissao_registro,
    SAFE_CAST(velocidade AS FLOAT64) AS velocidade,
    id_migracao_trajeto,
    sentido,
    trajeto,
    SAFE_CAST(hodometro AS FLOAT64) AS hodometro,
    direcao,
    ignicao='1' AS ignicao,
    SAFE_CAST(capacidadePeVeiculo AS INT64) AS capacidade_passageiros_pe,
    SAFE_CAST(capacidadeSentadoVeiculo AS INT64) AS capacidade_passageiros_sentados,
    DATETIME(SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%E6S%Ez', datetime_registro), 'America/Sao_Paulo') AS datahora_captura_registro,
    date AS data_captura_registro
FROM {{ source('brt_dataset', 'brt_bronze')}} WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {{ var('dias_historico_brt_silver') | int }} DAY)
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY codigo, datahora_emissao_registro
    ORDER BY datahora_captura_registro DESC) = 1


