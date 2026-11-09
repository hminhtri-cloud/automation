data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  azs = length(var.az_names) == 2 ? var.az_names : slice(data.aws_availability_zones.available.names, 0, 2)

  subnets = {
    public_az1 = { cidr = var.subnet_cidrs.public_az1, az = local.azs[0], tier = "public" }
    public_az2 = { cidr = var.subnet_cidrs.public_az2, az = local.azs[1], tier = "public" }
    app_az1    = { cidr = var.subnet_cidrs.app_az1, az = local.azs[0], tier = "app" }
    app_az2    = { cidr = var.subnet_cidrs.app_az2, az = local.azs[1], tier = "app" }
    db_az1     = { cidr = var.subnet_cidrs.db_az1, az = local.azs[0], tier = "db" }
    db_az2     = { cidr = var.subnet_cidrs.db_az2, az = local.azs[1], tier = "db" }
  }
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${var.project_name}-vpc" }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.project_name}-igw" }
}

resource "aws_subnet" "this" {
  for_each = local.subnets

  vpc_id                  = aws_vpc.this.id
  cidr_block              = each.value.cidr
  availability_zone       = each.value.az
  map_public_ip_on_launch = each.value.tier == "public"

  tags = {
    Name = "${var.project_name}-${replace(each.key, "_", "-")}"
    Tier = each.value.tier
  }
}

resource "aws_eip" "nat" {
  domain = "vpc"
  tags   = { Name = "${var.project_name}-nat-eip" }
}

resource "aws_nat_gateway" "this" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.this["public_az1"].id
  depends_on    = [aws_internet_gateway.this]
  tags          = { Name = "${var.project_name}-nat" }
}

resource "aws_route_table" "main" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.project_name}-main-rt" }
}

resource "aws_main_route_table_association" "this" {
  vpc_id         = aws_vpc.this.id
  route_table_id = aws_route_table.main.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = { Name = "${var.project_name}-public-rt" }
}

resource "aws_route_table" "app" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.this.id
  }

  tags = { Name = "${var.project_name}-private-app-rt" }
}

resource "aws_route_table" "db" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.project_name}-private-db-rt" }
}

resource "aws_route_table_association" "public" {
  for_each = toset(["public_az1", "public_az2"])

  subnet_id      = aws_subnet.this[each.key].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "app" {
  for_each = toset(["app_az1", "app_az2"])

  subnet_id      = aws_subnet.this[each.key].id
  route_table_id = aws_route_table.app.id
}

resource "aws_route_table_association" "db" {
  for_each = toset(["db_az1", "db_az2"])

  subnet_id      = aws_subnet.this[each.key].id
  route_table_id = aws_route_table.db.id
}
