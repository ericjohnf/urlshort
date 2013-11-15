drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  orig_url text not null,
  short text not null
);
