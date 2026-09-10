import 'package:equatable/equatable.dart';

/// Features for kidney disease risk prediction (UCI CKD benchmark).
class KidneyDiseaseRiskRequest extends Equatable {
  // 14 Numerical Features
  final double? age;
  final double? bp;
  final double? sg;
  final double? al;
  final double? su;
  final double? bgr;
  final double? bu;
  final double? sc;
  final double? sod;
  final double? pot;
  final double? hemo;
  final double? pcv;
  final double? wc;
  final double? rc;

  // 10 Categorical Features
  final String? rbc;
  final String? pc;
  final String? pcc;
  final String? ba;
  final String? htn;
  final String? dm;
  final String? cad;
  final String? appet;
  final String? pe;
  final String? ane;

  final bool isUserVerified;
  final int? reportId;

  const KidneyDiseaseRiskRequest({
    this.age,
    this.bp,
    this.sg,
    this.al,
    this.su,
    this.bgr,
    this.bu,
    this.sc,
    this.sod,
    this.pot,
    this.hemo,
    this.pcv,
    this.wc,
    this.rc,
    this.rbc,
    this.pc,
    this.pcc,
    this.ba,
    this.htn,
    this.dm,
    this.cad,
    this.appet,
    this.pe,
    this.ane,
    this.isUserVerified = true,
    this.reportId,
  });

  factory KidneyDiseaseRiskRequest.fromJson(Map<String, dynamic> json) {
    return KidneyDiseaseRiskRequest(
      age: (json['age'] as num?)?.toDouble(),
      bp: (json['bp'] as num?)?.toDouble(),
      sg: (json['sg'] as num?)?.toDouble(),
      al: (json['al'] as num?)?.toDouble(),
      su: (json['su'] as num?)?.toDouble(),
      bgr: (json['bgr'] as num?)?.toDouble(),
      bu: (json['bu'] as num?)?.toDouble(),
      sc: (json['sc'] as num?)?.toDouble(),
      sod: (json['sod'] as num?)?.toDouble(),
      pot: (json['pot'] as num?)?.toDouble(),
      hemo: (json['hemo'] as num?)?.toDouble(),
      pcv: (json['pcv'] as num?)?.toDouble(),
      wc: (json['wc'] as num?)?.toDouble(),
      rc: (json['rc'] as num?)?.toDouble(),
      rbc: json['rbc'] as String?,
      pc: json['pc'] as String?,
      pcc: json['pcc'] as String?,
      ba: json['ba'] as String?,
      htn: json['htn'] as String?,
      dm: json['dm'] as String?,
      cad: json['cad'] as String?,
      appet: json['appet'] as String?,
      pe: json['pe'] as String?,
      ane: json['ane'] as String?,
      isUserVerified: json['is_user_verified'] as bool? ?? true,
      reportId: (json['report_id'] as num?)?.toInt(),
    );
  }

  Map<String, dynamic> toJson() => {
        if (age != null) 'age': age,
        if (bp != null) 'bp': bp,
        if (sg != null) 'sg': sg,
        if (al != null) 'al': al,
        if (su != null) 'su': su,
        if (bgr != null) 'bgr': bgr,
        if (bu != null) 'bu': bu,
        if (sc != null) 'sc': sc,
        if (sod != null) 'sod': sod,
        if (pot != null) 'pot': pot,
        if (hemo != null) 'hemo': hemo,
        if (pcv != null) 'pcv': pcv,
        if (wc != null) 'wc': wc,
        if (rc != null) 'rc': rc,
        if (rbc != null) 'rbc': rbc,
        if (pc != null) 'pc': pc,
        if (pcc != null) 'pcc': pcc,
        if (ba != null) 'ba': ba,
        if (htn != null) 'htn': htn,
        if (dm != null) 'dm': dm,
        if (cad != null) 'cad': cad,
        if (appet != null) 'appet': appet,
        if (pe != null) 'pe': pe,
        if (ane != null) 'ane': ane,
        'is_user_verified': isUserVerified,
        if (reportId != null) 'report_id': reportId,
      };

  @override
  List<Object?> get props => [
        age,
        bp,
        sg,
        al,
        su,
        bgr,
        bu,
        sc,
        sod,
        pot,
        hemo,
        pcv,
        wc,
        rc,
        rbc,
        pc,
        pcc,
        ba,
        htn,
        dm,
        cad,
        appet,
        pe,
        ane,
        isUserVerified,
        reportId,
      ];
}
