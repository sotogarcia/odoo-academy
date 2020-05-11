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

 Date: 03/05/2020 17:22:17
*/


-- ----------------------------
-- Table structure for academy_public_tendering_public_offer
-- ----------------------------
DROP TABLE IF EXISTS "public"."academy_public_tendering_public_offer";
CREATE TABLE "public"."academy_public_tendering_public_offer" (
  "id" int4 NOT NULL DEFAULT nextval('academy_public_tendering_public_offer_id_seq'::regclass),
  "message_main_attachment_id" int4,
  "name" varchar(255) COLLATE "pg_catalog"."default" NOT NULL,
  "description" text COLLATE "pg_catalog"."default",
  "public_administration_id" int4 NOT NULL,
  "bulletin_board_url" varchar(256) COLLATE "pg_catalog"."default",
  "official_journal_url" varchar(256) COLLATE "pg_catalog"."default",
  "create_uid" int4,
  "create_date" timestamp(6),
  "write_uid" int4,
  "write_date" timestamp(6)
)
;
COMMENT ON COLUMN "public"."academy_public_tendering_public_offer"."message_main_attachment_id" IS 'Main Attachment';
COMMENT ON COLUMN "public"."academy_public_tendering_public_offer"."name" IS 'Name';
COMMENT ON COLUMN "public"."academy_public_tendering_public_offer"."description" IS 'Description';
COMMENT ON COLUMN "public"."academy_public_tendering_public_offer"."public_administration_id" IS 'Administration';
COMMENT ON COLUMN "public"."academy_public_tendering_public_offer"."bulletin_board_url" IS 'Bulletin Board';
COMMENT ON COLUMN "public"."academy_public_tendering_public_offer"."official_journal_url" IS 'Official journal';
COMMENT ON COLUMN "public"."academy_public_tendering_public_offer"."create_uid" IS 'Created by';
COMMENT ON COLUMN "public"."academy_public_tendering_public_offer"."create_date" IS 'Created on';
COMMENT ON COLUMN "public"."academy_public_tendering_public_offer"."write_uid" IS 'Last Updated by';
COMMENT ON COLUMN "public"."academy_public_tendering_public_offer"."write_date" IS 'Last Updated on';
COMMENT ON TABLE "public"."academy_public_tendering_public_offer" IS 'Academy public tendering public offer';

-- ----------------------------
-- Indexes structure for table academy_public_tendering_public_offer
-- ----------------------------
CREATE INDEX "academy_public_tendering_public_offer_message_main_attachment_i" ON "public"."academy_public_tendering_public_offer" USING btree (
  "message_main_attachment_id" "pg_catalog"."int4_ops" ASC NULLS LAST
);
CREATE INDEX "academy_public_tendering_public_offer_name_index" ON "public"."academy_public_tendering_public_offer" USING btree (
  "name" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table academy_public_tendering_public_offer
-- ----------------------------
ALTER TABLE "public"."academy_public_tendering_public_offer" ADD CONSTRAINT "academy_public_tendering_public_offer_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Foreign Keys structure for table academy_public_tendering_public_offer
-- ----------------------------
ALTER TABLE "public"."academy_public_tendering_public_offer" ADD CONSTRAINT "academy_public_tendering_public_message_main_attachment_id_fkey" FOREIGN KEY ("message_main_attachment_id") REFERENCES "public"."ir_attachment" ("id") ON DELETE SET NULL ON UPDATE NO ACTION;
ALTER TABLE "public"."academy_public_tendering_public_offer" ADD CONSTRAINT "academy_public_tendering_public_o_public_administration_id_fkey" FOREIGN KEY ("public_administration_id") REFERENCES "public"."academy_public_tendering_public_administration" ("id") ON DELETE CASCADE ON UPDATE NO ACTION;
ALTER TABLE "public"."academy_public_tendering_public_offer" ADD CONSTRAINT "academy_public_tendering_public_offer_create_uid_fkey" FOREIGN KEY ("create_uid") REFERENCES "public"."res_users" ("id") ON DELETE SET NULL ON UPDATE NO ACTION;
ALTER TABLE "public"."academy_public_tendering_public_offer" ADD CONSTRAINT "academy_public_tendering_public_offer_write_uid_fkey" FOREIGN KEY ("write_uid") REFERENCES "public"."res_users" ("id") ON DELETE SET NULL ON UPDATE NO ACTION;
