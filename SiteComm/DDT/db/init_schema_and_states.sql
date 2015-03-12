drop table if exists bidirectional_links;
drop table if exists link_metrics_items;
drop table if exists links;
drop table if exists states;
drop table if exists nodes;


create table nodes (
		id             int        not null auto_increment,
		name					 varchar(50),
		primary key(id)
);

create table states (
    id             int          not null auto_increment,
		name           varchar(50),
		primary key(id)
);

create table links (
    id             int        not null auto_increment,
    from_node_id   int,
    to_node_id     int,
		state_id       int,
		constraint fk_links_state foreign key (state_id) references states(id),
		constraint fk_link_from_node foreign key (from_node_id) references nodes(id),
		constraint fk_link_to_node foreign key (to_node_id) references nodes(id),
		primary key(id)
);


create table link_metrics_items (
    id             					int          not null auto_increment,
		original_metrics_value  float,
		date										datetime,
		link_id									int,
		constraint fk_link_link_metrics_items foreign key (link_id) references links(id),
		primary key(id)
);


create table bidirectional_links (
		id             int        not null auto_increment,
		from_link_id	 int,
		to_link_id		 int,
		from_node_id	 int,
		to_node_id		 int,
		constraint fk_bdlink_fromlink foreign key (from_link_id) references links(id),
		constraint fk_bdlink_tolink foreign key (to_link_id) references links(id),
		constraint fk_bdlink_fromnode foreign key (from_node_id) references nodes(id),
		constraint fk_bdlink_tonode foreign key (to_node_id) references nodes(id),		
		primary key(id)
);




INSERT INTO `states` VALUES (1,'COMMISSIONED');
INSERT INTO `states` VALUES (2,'NOT-TESTED');
INSERT INTO `states` VALUES (3,'PENDING-COMMISSIONING');
INSERT INTO `states` VALUES (4,'PENDING-RATE');
INSERT INTO `states` VALUES (5,'PROBLEM-RATE');
INSERT INTO `states` VALUES (6,'SUSPENDED');

