/*
 Navicat Premium Data Transfer

 Source Server         : localhost
 Source Server Type    : PostgreSQL
 Source Server Version : 120001
 Source Host           : localhost:5432
 Source Catalog        : odoo_postal_dev
 Source Schema         : public

 Target Server Type    : PostgreSQL
 Target Server Version : 120001
 File Encoding         : 65001

 Date: 03/05/2020 17:22:37
*/


-- ----------------------------
-- Table structure for academy_public_tendering_process
-- ----------------------------
DROP TABLE IF EXISTS "public"."academy_public_tendering_process";
CREATE TABLE "public"."academy_public_tendering_process" (
  "id" int4 NOT NULL DEFAULT nextval('academy_public_tendering_process_id_seq'::regclass),
  "message_main_attachment_id" int4,
  "name" varchar(255) COLLATE "pg_catalog"."default" NOT NULL,
  "description" text COLLATE "pg_catalog"."default",
  "active" bool,
  "public_tendering_public_offer_id" int4 NOT NULL,
  "employment_group_id" int4 NOT NULL,
  "public_corps_id" int4 NOT NULL,
  "exam_type_id" int4 NOT NULL,
  "hiring_type_id" int4 NOT NULL,
  "access_system_id" int4 NOT NULL,
  "target_date" date,
  "bulletin_board_url" varchar(256) COLLATE "pg_catalog"."default",
  "official_journal_url" varchar(256) COLLATE "pg_catalog"."default",
  "state_id" int4 NOT NULL,
  "create_uid" int4,
  "create_date" timestamp(6),
  "write_uid" int4,
  "write_date" timestamp(6)
)
;
COMMENT ON COLUMN "public"."academy_public_tendering_process"."message_main_attachment_id" IS 'Main Attachment';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."name" IS 'Denomination';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."description" IS 'Description';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."active" IS 'Active';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."public_tendering_public_offer_id" IS 'Public offer';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."employment_group_id" IS 'Group';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."public_corps_id" IS 'Corps';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."exam_type_id" IS 'Exam type';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."hiring_type_id" IS 'Hiring type';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."access_system_id" IS 'Access system';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."target_date" IS 'Due date';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."bulletin_board_url" IS 'Bulletin Board';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."official_journal_url" IS 'Official journal';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."state_id" IS 'State';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."create_uid" IS 'Created by';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."create_date" IS 'Created on';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."write_uid" IS 'Last Updated by';
COMMENT ON COLUMN "public"."academy_public_tendering_process"."write_date" IS 'Last Updated on';
COMMENT ON TABLE "public"."academy_public_tendering_process" IS 'Public tendering';

-- ----------------------------
-- Indexes structure for table academy_public_tendering_process
-- ----------------------------
CREATE INDEX "academy_public_tendering_process_message_main_attachment_id_ind" ON "public"."academy_public_tendering_process" USING btree (
  "message_main_attachment_id" "pg_catalog"."int4_ops" ASC NULLS LAST
);
CREATE INDEX "academy_public_tendering_process_name_index" ON "public"."academy_public_tendering_process" USING btree (
  "name" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table academy_public_tendering_process
-- ----------------------------
ALTER TABLE "public"."academy_public_tendering_process" ADD CONSTRAINT "academy_public_tendering_process_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Foreign Keys structure for table academy_public_tendering_process
-- ----------------------------
ALTER TABLE "public"."academy_public_tendering_process" ADD CONSTRAINT "academy_public_tendering_proc_public_tendering_public_offe_fkey" FOREIGN KEY ("public_tendering_public_offer_id") REFERENCES "public"."academy_public_tendering_public_offer" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."academy_public_tendering_process" ADD CONSTRAINT "academy_public_tendering_proces_message_main_attachment_id_fkey" FOREIGN KEY ("message_main_attachment_id") REFERENCES "public"."ir_attachment" ("id") ON DELETE SET NULL ON UPDATE NO ACTION;
ALTER TABLE "public"."academy_public_tendering_process" ADD CONSTRAINT "academy_public_tendering_process_access_system_id_fkey" FOREIGN KEY ("access_system_id") REFERENCES "public"."academy_public_tendering_access_system" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."academy_public_tendering_process" ADD CONSTRAINT "academy_public_tendering_process_create_uid_fkey" FOREIGN KEY ("create_uid") REFERENCES "public"."res_users" ("id") ON DELETE SET NULL ON UPDATE NO ACTION;
ALTER TABLE "public"."academy_public_tendering_process" ADD CONSTRAINT "academy_public_tendering_process_employment_group_id_fkey" FOREIGN KEY ("employment_group_id") REFERENCES "public"."academy_public_tendering_employment_group" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."academy_public_tendering_process" ADD CONSTRAINT "academy_public_tendering_process_exam_type_id_fkey" FOREIGN KEY ("exam_type_id") REFERENCES "public"."academy_public_tendering_exam_type" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."academy_public_tendering_process" ADD CONSTRAINT "academy_public_tendering_process_hiring_type_id_fkey" FOREIGN KEY ("hiring_type_id") REFERENCES "public"."academy_public_tendering_hiring_type" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."academy_public_tendering_process" ADD CONSTRAINT "academy_public_tendering_process_public_corps_id_fkey" FOREIGN KEY ("public_corps_id") REFERENCES "public"."academy_public_tendering_corps" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."academy_public_tendering_process" ADD CONSTRAINT "academy_public_tendering_process_state_id_fkey" FOREIGN KEY ("state_id") REFERENCES "public"."academy_public_tendering_event_type" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."academy_public_tendering_process" ADD CONSTRAINT "academy_public_tendering_process_write_uid_fkey" FOREIGN KEY ("write_uid") REFERENCES "public"."res_users" ("id") ON DELETE SET NULL ON UPDATE NO ACTION;
