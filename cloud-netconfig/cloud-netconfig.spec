#
# spec file for package cloud-netconfig
#
# Copyright (c) 2017 SUSE Linux GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#

%define base_name cloud-netconfig

%if "@BUILD_FLAVOR@" == ""
%define flavor_suffix %nil
%define csp_string None
ExclusiveArch:  do-not-build
%endif
%if "@BUILD_FLAVOR@" == "azure"
%define flavor_suffix -azure
%define csp_string Microsoft Azure
Provides:       cloud-netconfig
Conflicts:      otherproviders(cloud-netconfig)
%endif
%if "@BUILD_FLAVOR@" == "ec2"
%define flavor_suffix -ec2
%define csp_string Amazon EC2
Provides:       cloud-netconfig
Conflicts:      otherproviders(cloud-netconfig)
%endif

Name:           %{base_name}%{flavor_suffix}
Version:        0.6
Release:        0
License:        GPL-3.0+
Summary:        Network configuration scripts for %{csp_string}
Url:            https://github.com/SUSE/Enceladus
Group:          System/Management
Source0:        %{base_name}-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch
%if 0%{?suse_version} == 1110
BuildRequires:  sysconfig
Requires:       sysconfig
%define _udevrulesdir %{_sysconfdir}/udev/rules.d
%else
BuildRequires:  sysconfig-netconfig
Requires:       sysconfig-netconfig
%endif
BuildRequires:  udev
Requires:       udev
# persistent net generator was split off from udev in Leap
%if 0%{?leap_version} != 0
Requires:       udev-persistent-ifnames
%endif

%description -n %{base_name}%{flavor_suffix}
This package contains scripts for automatically configuring network interfaces
in %{csp_string} with full support for hotplug.

%prep
%setup -q -n %{base_name}-%{version}

%build

%install
make install%{flavor_suffix} \
  DESTDIR=%{buildroot} \
  PREFIX=%{_usr} \
  SYSCONFDIR=%{_sysconfdir} \
  UDEVRULESDIR=%{_udevrulesdir}

# Disable persistent net generator from udev-persistent-ifnames as
# it does not work for xen interfaces. This will likely produce a warning.
%if 0%{?suse_version} >= 1315
mkdir -p %{buildroot}/%{_sysconfdir}/udev/rules.d
ln -s /dev/null %{buildroot}/%{_sysconfdir}/udev/rules.d/75-persistent-net-generator.rules
%endif

%files -n %{base_name}%{flavor_suffix}
%defattr(-,root,root)
%{_sysconfdir}/netconfig.d/cloud-netconfig
%{_sysconfdir}/sysconfig/network/scripts/*
%if 0%{?suse_version} >= 1315
%{_sysconfdir}/udev/rules.d
%endif
%{_udevrulesdir}/*
%doc README.md LICENSE

%changelog
