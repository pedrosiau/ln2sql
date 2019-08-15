CREATE TABLE `users` (
  `id` integer NOT NULL,
  `name` character varying NOT NULL,
  `score` integer DEFAULT 0,
);

ALTER TABLE `users`
  ADD PRIMARY KEY `id`
  ADD KEY `id` (`id`);

CREATE TABLE `enrollments` (
  `id` integer NOT NULL,
  `user_id` integer,
  `classroom_id` integer,
  `created_at` timestamp with time zone DEFAULT now() NOT NULL,
  `updated_at` timestamp with time zone DEFAULT now() NOT NULL,
  `disabled` timestamp with time zone,
  `approved` boolean
);

ALTER TABLE `enrollments`
  ADD PRIMARY KEY `id`
  ADD KEY `user_id` (`user_id`);

ALTER TABLE `enrollments`
  ADD CONSTRAINT `enrollments_idfk` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

CREATE TABLE `contracts` (
  `id` integer NOT NULL,
  `user_id` integer,
  `date` timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE `contracts`
  ADD PRIMARY KEY `id`
  ADD KEY `user_id` (`user_id`);

ALTER TABLE `contracts`
  ADD CONSTRAINT `contracts_idfk` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
