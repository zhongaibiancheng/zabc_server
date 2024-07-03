drop database zhong_ai_bian_cheng;

create database zhong_ai_bian_cheng;

--Dora@20f
create user zhong_ai_bian_cheng_user01;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO zhong_ai_bian_cheng_user01;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO zhong_ai_bian_cheng_user01;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO zhong_ai_bian_cheng_user01;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO zhong_ai_bian_cheng_user01;


grant connect on database zhong_ai_bian_cheng to zhong_ai_bian_cheng_user01;

\ c zhong_ai_bian_cheng;

drop table quiz;
create table quiz(
    id serial PRIMARY KEY NOT NULL,
    no int not null,
    title text not null,
    difficulty int not null,
    source varchar(256) not null,
    remark varchar(1024),
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    deleted_at timestamp with time zone,
    delete_flg int not null default 0
);

GRANT ALL ON quiz TO zhong_ai_bian_cheng_user01;
GRANT SELECT,INSERT,UPDATE,DELETE ON quiz_id_seq TO zhong_ai_bian_cheng_user01;
GRANT ALL ON master_knowledge TO zhong_ai_bian_cheng_user01;
GRANT SELECT,INSERT,UPDATE,DELETE ON master_knowledge_id_seq TO zhong_ai_bian_cheng_user01;



drop table quiz_knowledge;
create table quiz_knowledge(
    id serial PRIMARY KEY NOT NULL,
    quiz_id int not null,
    knowledge_id int not null,
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    deleted_at timestamp with time zone,
    delete_flg int not null default 0
);

drop table master_knowledge;
create table master_knowledge(
    id serial PRIMARY KEY NOT NULL,
    title varchar(1024) not null,
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    deleted_at timestamp with time zone,
    delete_flg int not null default 0
);

insert into master_knowledge(title,created_at,updated_at,delete_flg)values('顺序性',now(),now(),0);
insert into master_knowledge(title,created_at,updated_at,delete_flg)values('输入',now(),now(),0);
insert into master_knowledge(title,created_at,updated_at,delete_flg)values('输出',now(),now(),0);
insert into master_knowledge(title,created_at,updated_at,delete_flg)values('分支',now(),now(),0);
insert into master_knowledge(title,created_at,updated_at,delete_flg)values('循环',now(),now(),0);
insert into master_knowledge(title,created_at,updated_at,delete_flg)values('递归',now(),now(),0);
insert into master_knowledge(title,created_at,updated_at,delete_flg)values('字符串',now(),now(),0);
insert into master_knowledge(title,created_at,updated_at,delete_flg)values('数组',now(),now(),0);
