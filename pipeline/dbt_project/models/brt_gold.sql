{{
    config(
        materialized='incremental',
        unique_key="codigo_datahora",
        partition_by={
        "field": "DATE(datahora_captura_registro)",
        "data_type": "date"
        },
        cluster_by=["linha","codigo"],
        merge_update_partition_filter="DATE(datahora_captura_registro) >= DATE_SUB(CURRENT_DATE(), INTERVAL {{ var('dias_historico_brt_silver') | int }} DAY)"
    )
}}

SELECT 
    codigo,
    placa,
    linha,
    latitude,
    longitude,
    datahora_emissao_registro,
    velocidade,
    id_migracao_trajeto,
    sentido,
    trajeto,
    hodometro,
    direcao,
    ignicao,
    datahora_captura_registro,
    CONCAT(codigo, '_', CAST(datahora_emissao_registro AS STRING)) AS codigo_datahora
FROM {{ ref('brt_silver') }}
{% if is_incremental() %}
WHERE datahora_captura_registro > (SELECT MAX(datahora_captura_registro) FROM {{ this }})
{% endif %} 
