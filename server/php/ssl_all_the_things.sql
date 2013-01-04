

create database ssl_all_the_things;

use ssl_all_the_things;

CREATE TABLE certificates (
    cert_id         INT                   NOT NULL AUTO_INCREMENT,
    subject         VARCHAR(255)          NOT NULL,
    issuer          VARCHAR(255)          NOT NULL,
    is_ca           INT                   NOT NULL,
    serialnr        VARCHAR(255)          NOT NULL,
    valid_from      DATETIME              NULL,
    valid_until     DATETIME              NULL,

    PRIMARY KEY (cert_id),
    UNIQUE (subject, issuer, serialnr),
    INDEX (subject)
    );


create table ipv4_result (
    oct_a INT,
    oct_b INT,
    oct_c INT,
    oct_d INT,
    cert_id INT,
    created TIMESTAMP DEFAULT NOW(),
    cur_timestamp TIMESTAMP
    );

create table ipv4_dispatch (
    oct_a INT,
    oct_b INT,
    oct_c INT,
    oct_d INT,
    status VARCHAR(1),
    cur_timestamp TIMESTAMP
    );


