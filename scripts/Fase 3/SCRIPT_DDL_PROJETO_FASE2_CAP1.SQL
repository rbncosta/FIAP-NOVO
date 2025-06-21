-- Gerado por Oracle SQL Developer Data Modeler 24.3.1.351.0831
--   em:        2025-04-15 21:42:57 BRT
--   site:      Oracle Database 11g
--   tipo:      Oracle Database 11g



DROP TABLE T_APLICACOES CASCADE CONSTRAINTS 
;

DROP TABLE T_CULTURAS CASCADE CONSTRAINTS 
;

DROP TABLE T_MEDICOES CASCADE CONSTRAINTS 
;

DROP TABLE T_SENSORES CASCADE CONSTRAINTS 
;

DROP TABLE T_SUGESTOES CASCADE CONSTRAINTS 
;

-- predefined type, no DDL - MDSYS.SDO_GEOMETRY

-- predefined type, no DDL - XMLTYPE

CREATE TABLE T_APLICACOES 
    ( 
     cod_medicao          NUMBER (3)  NOT NULL , 
     cod_sugestao         NUMBER (3)  NOT NULL , 
     cod_sensor           NUMBER (3)  NOT NULL , 
     cod_cultura          NUMBER (3)  NOT NULL , 
     cod_aplicacao        NUMBER (3)  NOT NULL , 
     nm_produto_utilizado VARCHAR2 (30)  NOT NULL , 
     valor_aplicacao      NUMBER (5,2)  NOT NULL , 
     un_aplicacao         CHAR (2)  NOT NULL , 
     data_hora_aplicacao  TIMESTAMP WITH LOCAL TIME ZONE  NOT NULL , 
     nm_resp_aplicacao    VARCHAR2 (30)  NOT NULL , 
     documento_resp       CHAR (11)  NOT NULL 
    ) 
;
CREATE UNIQUE INDEX APLIC__IDX ON T_APLICACOES 
    ( 
     cod_sugestao ASC , 
     cod_medicao ASC , 
     cod_sensor ASC 
    ) 
;

ALTER TABLE T_APLICACOES 
    ADD CONSTRAINT PK_APLIC PRIMARY KEY ( cod_aplicacao, cod_medicao, cod_sugestao, cod_sensor ) ;

CREATE TABLE T_CULTURAS 
    ( 
     cod_cultura        NUMBER (3)  NOT NULL , 
     desc_cultura       VARCHAR2 (30)  NOT NULL , 
     tamanho_cultura    NUMBER (7,2)  NOT NULL , 
     data_prev_colheita DATE 
    ) 
;

ALTER TABLE T_CULTURAS 
    ADD CONSTRAINT PK_CUL PRIMARY KEY ( cod_cultura ) ;

ALTER TABLE T_CULTURAS 
    ADD CONSTRAINT UN_CULTURAS_DEC UNIQUE ( desc_cultura ) ;

CREATE TABLE T_MEDICOES 
    ( 
     cod_medicao       NUMBER (3)  NOT NULL , 
     data_hora_medicao TIMESTAMP WITH LOCAL TIME ZONE  NOT NULL , 
     valor_medicao     NUMBER (5,2)  NOT NULL , 
     un_medicao        CHAR (2)  NOT NULL , 
     cod_sensor        NUMBER (3)  NOT NULL 
    ) 
;

ALTER TABLE T_MEDICOES 
    ADD CONSTRAINT PK_MED PRIMARY KEY ( cod_medicao, cod_sensor ) ;

CREATE TABLE T_SENSORES 
    ( 
     cod_sensor           NUMBER (3)  NOT NULL , 
     nm_sensor            VARCHAR2 (30)  NOT NULL , 
     tipo_sensor          CHAR (2)  NOT NULL , 
     objetivo_sensor      VARCHAR2 (30) , 
     fab_sensor           VARCHAR2 (30)  NOT NULL , 
     modelo_sensor        VARCHAR2 (30)  NOT NULL , 
     data_instalacao      DATE  NOT NULL , 
     latitude_instalacao  NUMBER  NOT NULL , 
     longitude_instalacao NUMBER  NOT NULL , 
     valor_minimo         NUMBER (5,2)  NOT NULL , 
     valor_maximo         NUMBER (5,2)  NOT NULL , 
     unidade              CHAR (2)  NOT NULL , 
     cod_cultura          NUMBER (3)  NOT NULL 
    ) 
;

ALTER TABLE T_SENSORES 
    ADD CONSTRAINT CK_SENSORES_VLRMIN 
    CHECK (valor_minimo > 0)
;


ALTER TABLE T_SENSORES 
    ADD CONSTRAINT CK_SENSORES_VLRMAX 
    CHECK (valor_maximo > 0)
;
ALTER TABLE T_SENSORES 
    ADD CONSTRAINT PK_SENS PRIMARY KEY ( cod_sensor ) ;

ALTER TABLE T_SENSORES 
    ADD CONSTRAINT UN_SENSORES_NOME UNIQUE ( nm_sensor ) ;

ALTER TABLE T_SENSORES 
    ADD CONSTRAINT UN_SENSORES_LATITUDE UNIQUE ( latitude_instalacao ) ;

ALTER TABLE T_SENSORES 
    ADD CONSTRAINT UN_SENSORES_LONGITUDE UNIQUE ( longitude_instalacao ) ;

CREATE TABLE T_SUGESTOES 
    ( 
     cod_medicao        NUMBER (3)  NOT NULL , 
     cod_sugestao       NUMBER (3)  NOT NULL , 
     objetivo_sugestao  VARCHAR2 (30)  NOT NULL , 
     data_hora_sugestao TIMESTAMP WITH LOCAL TIME ZONE  NOT NULL , 
     valor_sugestao     NUMBER (5,2)  NOT NULL , 
     un_sugestao        CHAR (2)  NOT NULL , 
     cod_sensor         NUMBER (3)  NOT NULL 
    ) 
;
CREATE UNIQUE INDEX T_SUG__IDX ON T_SUGESTOES 
    ( 
     cod_medicao ASC , 
     cod_sensor ASC 
    ) 
;

ALTER TABLE T_SUGESTOES 
    ADD CONSTRAINT PK_SUG PRIMARY KEY ( cod_sugestao, cod_medicao, cod_sensor ) ;

ALTER TABLE T_APLICACOES 
    ADD CONSTRAINT FK_APLIC_CUL FOREIGN KEY 
    ( 
     cod_cultura
    ) 
    REFERENCES T_CULTURAS 
    ( 
     cod_cultura
    ) 
;

ALTER TABLE T_APLICACOES 
    ADD CONSTRAINT FK_APLIC_SUG FOREIGN KEY 
    ( 
     cod_sugestao,
     cod_medicao,
     cod_sensor
    ) 
    REFERENCES T_SUGESTOES 
    ( 
     cod_sugestao,
     cod_medicao,
     cod_sensor
    ) 
;

ALTER TABLE T_MEDICOES 
    ADD CONSTRAINT FK_MED_SENS FOREIGN KEY 
    ( 
     cod_sensor
    ) 
    REFERENCES T_SENSORES 
    ( 
     cod_sensor
    ) 
;

ALTER TABLE T_SENSORES 
    ADD CONSTRAINT FK_SENS_CUL FOREIGN KEY 
    ( 
     cod_cultura
    ) 
    REFERENCES T_CULTURAS 
    ( 
     cod_cultura
    ) 
;

ALTER TABLE T_SUGESTOES 
    ADD CONSTRAINT FK_SUG_MED FOREIGN KEY 
    ( 
     cod_medicao,
     cod_sensor
    ) 
    REFERENCES T_MEDICOES 
    ( 
     cod_medicao,
     cod_sensor
    ) 
;



-- Relatório do Resumo do Oracle SQL Developer Data Modeler: 
-- 
-- CREATE TABLE                             5
-- CREATE INDEX                             2
-- ALTER TABLE                             16
-- CREATE VIEW                              0
-- ALTER VIEW                               0
-- CREATE PACKAGE                           0
-- CREATE PACKAGE BODY                      0
-- CREATE PROCEDURE                         0
-- CREATE FUNCTION                          0
-- CREATE TRIGGER                           0
-- ALTER TRIGGER                            0
-- CREATE COLLECTION TYPE                   0
-- CREATE STRUCTURED TYPE                   0
-- CREATE STRUCTURED TYPE BODY              0
-- CREATE CLUSTER                           0
-- CREATE CONTEXT                           0
-- CREATE DATABASE                          0
-- CREATE DIMENSION                         0
-- CREATE DIRECTORY                         0
-- CREATE DISK GROUP                        0
-- CREATE ROLE                              0
-- CREATE ROLLBACK SEGMENT                  0
-- CREATE SEQUENCE                          0
-- CREATE MATERIALIZED VIEW                 0
-- CREATE MATERIALIZED VIEW LOG             0
-- CREATE SYNONYM                           0
-- CREATE TABLESPACE                        0
-- CREATE USER                              0
-- 
-- DROP TABLESPACE                          0
-- DROP DATABASE                            0
-- 
-- REDACTION POLICY                         0
-- 
-- ORDS DROP SCHEMA                         0
-- ORDS ENABLE SCHEMA                       0
-- ORDS ENABLE OBJECT                       0
-- 
-- ERRORS                                   0
-- WARNINGS                                 0
